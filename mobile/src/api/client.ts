import type { ApiErrorBody } from './types'
import { tokenStorage } from './tokenStorage'
import { rewriteLocalhostToLan } from '@/lib/lanHost'

const configured = (process.env.EXPO_PUBLIC_API_BASE_URL ?? '').replace(/\/$/, '')
const rawBase = configured.length > 0 ? configured : 'http://localhost:8000/api/v1'

export const API_BASE_URL = rewriteLocalhostToLan(rawBase)

export class ApiError extends Error {
  readonly status: number
  readonly code: string
  readonly details: Record<string, unknown>
  readonly body: ApiErrorBody | null

  constructor(
    status: number,
    message: string,
    options?: {
      code?: string
      details?: Record<string, unknown>
      body?: ApiErrorBody | null
    },
  ) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.code = options?.code ?? 'UNKNOWN'
    this.details = options?.details ?? {}
    this.body = options?.body ?? null
  }
}

export class NetworkError extends Error {
  readonly reason: 'offline' | 'unreachable'

  constructor(reason: 'offline' | 'unreachable', message: string) {
    super(message)
    this.name = 'NetworkError'
    this.reason = reason
  }
}

export function isNetworkFailure(err: unknown): boolean {
  return err instanceof NetworkError || err instanceof TypeError
}

type RequestOptions = Omit<RequestInit, 'body'> & {
  body?: unknown
  skipAuthRefresh?: boolean
  auth?: boolean
}

const REQUEST_TIMEOUT_MS = 8000

let refreshPromise: Promise<boolean> | null = null

async function fetchWithTimeout(url: string, init: RequestInit): Promise<Response> {
  const controller = new AbortController()
  const timer = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS)
  try {
    return await fetch(url, { ...init, signal: controller.signal })
  } catch (err) {
    if (err instanceof Error && err.name === 'AbortError') {
      throw new TypeError(`Przekroczono limit ${REQUEST_TIMEOUT_MS} ms`)
    }
    throw err
  } finally {
    clearTimeout(timer)
  }
}

function firstValidationMessage(body: ApiErrorBody | null): string | null {
  if (!body) {
    return null
  }
  if (body.error?.message) {
    return body.error.message
  }
  if (typeof body.detail === 'string') {
    return body.detail
  }

  for (const [key, value] of Object.entries(body)) {
    if (key === 'error' || key === 'detail') {
      continue
    }
    if (typeof value === 'string') {
      return value
    }
    if (Array.isArray(value) && typeof value[0] === 'string') {
      return value[0]
    }
    if (value && typeof value === 'object' && !Array.isArray(value)) {
      const nested = firstValidationMessage(value as ApiErrorBody)
      if (nested) {
        return nested
      }
    }
  }
  return null
}

function parseErrorMessage(status: number, body: ApiErrorBody | null): string {
  const fromBody = firstValidationMessage(body)
  if (fromBody) {
    return fromBody
  }
  if (status === 401) {
    return 'Sesja wygasła. Zaloguj się ponownie.'
  }
  if (status === 403) {
    return 'Brak uprawnień do tego zasobu.'
  }
  if (status === 404) {
    return 'Nie znaleziono zasobu.'
  }
  if (status === 409) {
    return 'Konflikt danych (np. kolizja terminu).'
  }
  if (status >= 500) {
    return 'Błąd serwera. Spróbuj ponownie później.'
  }
  return 'Wystąpił nieoczekiwany błąd.'
}

async function parseJson(response: Response): Promise<ApiErrorBody | null> {
  const text = await response.text()
  if (!text) {
    return null
  }
  try {
    return JSON.parse(text) as ApiErrorBody
  } catch {
    return null
  }
}

function offlineMessage(): string {
  return 'Brak połączenia z internetem. Sprawdź sieć i spróbuj ponownie.'
}

function unreachableMessage(): string {
  if (__DEV__) {
    return `Nie udało się połączyć z API (${API_BASE_URL}). Na telefonie ustaw EXPO_PUBLIC_API_BASE_URL na IP komputera, nie localhost.`
  }
  return 'Nie udało się połączyć z serwerem. Sprawdź połączenie internetowe i spróbuj ponownie.'
}

async function detectOffline(): Promise<boolean> {
  try {
    const NetInfo = (await import('@react-native-community/netinfo')).default
    const state = await NetInfo.fetch()
    if (state.isConnected === false) {
      return true
    }
    if (state.isInternetReachable === false) {
      return true
    }
    return false
  } catch {
    return false
  }
}

async function toNetworkError(cause: unknown): Promise<NetworkError> {
  const offline = await detectOffline()
  if (offline) {
    return new NetworkError('offline', offlineMessage())
  }
  const fallback = unreachableMessage()
  if (cause instanceof Error && cause.message && __DEV__) {
    return new NetworkError('unreachable', `${fallback} (${cause.message})`)
  }
  return new NetworkError('unreachable', fallback)
}

async function tryRefreshSession(): Promise<boolean> {
  if (refreshPromise) {
    return refreshPromise
  }

  refreshPromise = (async () => {
    try {
      const refresh = await tokenStorage.getRefresh()
      if (!refresh) {
        return false
      }
      const response = await fetchWithTimeout(`${API_BASE_URL}/auth/refresh/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
        body: JSON.stringify({ refresh }),
      })
      if (!response.ok) {
        await tokenStorage.clear()
        return false
      }
      const data = (await response.json()) as { access?: string; refresh?: string }
      if (!data.access) {
        await tokenStorage.clear()
        return false
      }
      await tokenStorage.setTokens(data.access, data.refresh ?? refresh)
      return true
    } catch {
      return false
    } finally {
      refreshPromise = null
    }
  })()

  return refreshPromise
}

export async function apiRequest<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { body, skipAuthRefresh, auth = true, headers: customHeaders, ...rest } = options
  const headers = new Headers(customHeaders)
  headers.set('Accept', 'application/json')

  if (auth) {
    const access = await tokenStorage.getAccess()
    if (access) {
      headers.set('Authorization', `Bearer ${access}`)
    }
  }

  let payload: BodyInit | undefined
  if (body !== undefined && body !== null) {
    if (body instanceof FormData) {
      payload = body
    } else {
      headers.set('Content-Type', 'application/json')
      payload = JSON.stringify(body)
    }
  }

  const url = path.startsWith('http')
    ? path
    : `${API_BASE_URL}${path.startsWith('/') ? path : `/${path}`}`

  if (await detectOffline()) {
    throw new NetworkError('offline', offlineMessage())
  }

  let response: Response
  try {
    response = await fetchWithTimeout(url, {
      ...rest,
      headers,
      body: payload,
    })
  } catch (err) {
    throw await toNetworkError(err)
  }

  if (response.status === 401 && auth && !skipAuthRefresh) {
    const refreshed = await tryRefreshSession()
    if (refreshed) {
      return apiRequest<T>(path, { ...options, skipAuthRefresh: true })
    }
  }

  if (response.status === 204) {
    return undefined as T
  }

  const data = await parseJson(response)

  if (!response.ok) {
    throw new ApiError(response.status, parseErrorMessage(response.status, data), {
      code: data?.error?.code,
      details: data?.error?.details,
      body: data,
    })
  }

  return data as T
}

export function getErrorMessage(err: unknown, fallback: string): string {
  if (err instanceof NetworkError) {
    return err.message
  }
  if (err instanceof ApiError) {
    return err.message
  }
  if (err instanceof TypeError) {
    return unreachableMessage()
  }
  if (err instanceof Error && err.message) {
    return err.message
  }
  return fallback
}

export function getFieldError(err: unknown, field: string): string | null {
  if (!(err instanceof ApiError)) {
    return null
  }
  const value = err.details?.[field]
  if (typeof value === 'string' && value.trim()) {
    return value
  }
  if (Array.isArray(value) && typeof value[0] === 'string' && value[0].trim()) {
    return value[0]
  }
  return null
}

export const api = {
  get: <T>(path: string, options?: RequestOptions) =>
    apiRequest<T>(path, { ...options, method: 'GET' }),

  post: <T>(path: string, body?: unknown, options?: RequestOptions) =>
    apiRequest<T>(path, { ...options, method: 'POST', body }),

  patch: <T>(path: string, body?: unknown, options?: RequestOptions) =>
    apiRequest<T>(path, { ...options, method: 'PATCH', body }),

  put: <T>(path: string, body?: unknown, options?: RequestOptions) =>
    apiRequest<T>(path, { ...options, method: 'PUT', body }),

  delete: <T>(path: string, options?: RequestOptions) =>
    apiRequest<T>(path, { ...options, method: 'DELETE' }),
}
