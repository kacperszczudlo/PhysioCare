import type { ApiErrorBody } from './types'

const configuredBase = (import.meta.env.VITE_API_BASE_URL as string | undefined)?.replace(/\/$/, '')

export const API_BASE_URL = configuredBase && configuredBase.length > 0 ? configuredBase : '/api/v1'

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

type RequestOptions = Omit<RequestInit, 'body'> & {
  body?: unknown
  skipAuthRefresh?: boolean
}

let refreshPromise: Promise<boolean> | null = null

/** Odświeża access cookie (używane też przez SSE reconnect). */
export async function refreshAccessToken(): Promise<boolean> {
  if (refreshPromise) {
    return refreshPromise
  }

  refreshPromise = (async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/auth/refresh/`, {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
        body: JSON.stringify({}),
      })
      return response.ok
    } catch {
      return false
    } finally {
      refreshPromise = null
    }
  })()

  return refreshPromise
}

async function tryRefreshSession(): Promise<boolean> {
  return refreshAccessToken()
}

const GENERIC_API_MESSAGES = new Set([
  'Walidacja nie powiodła się.',
  'Wystąpił błąd.',
  'Wystąpił nieoczekiwany błąd.',
  'Wystąpił nieoczekiwany błąd serwera.',
  'Wystąpił nieoczekiwany błąd serwera. Szczegóły są w logach backendu.',
])

function firstFieldMessage(details: unknown): string | null {
  if (!details || typeof details !== 'object') {
    return null
  }
  if (Array.isArray(details)) {
    return typeof details[0] === 'string' ? details[0] : null
  }

  for (const value of Object.values(details as Record<string, unknown>)) {
    if (typeof value === 'string' && value.trim()) {
      return value
    }
    if (Array.isArray(value) && typeof value[0] === 'string' && value[0].trim()) {
      return value[0]
    }
    if (value && typeof value === 'object') {
      const nested = firstFieldMessage(value)
      if (nested) {
        return nested
      }
    }
  }
  return null
}

function firstValidationMessage(body: ApiErrorBody | null): string | null {
  if (!body) {
    return null
  }

  const fromDetails = firstFieldMessage(body.error?.details)
  if (fromDetails) {
    return fromDetails
  }

  if (body.error?.message && !GENERIC_API_MESSAGES.has(body.error.message)) {
    return body.error.message
  }
  if (typeof body.detail === 'string' && body.detail.trim()) {
    return body.detail
  }

  for (const [key, value] of Object.entries(body)) {
    if (key === 'error' || key === 'detail') {
      continue
    }
    const nested = firstFieldMessage(value)
    if (nested) {
      return nested
    }
  }

  if (body.error?.message) {
    return body.error.message
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

export async function apiRequest<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { body, skipAuthRefresh, headers: customHeaders, ...rest } = options
  const headers = new Headers(customHeaders)
  headers.set('Accept', 'application/json')

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

  const response = await fetch(url, {
    ...rest,
    headers,
    body: payload,
    credentials: 'include',
  })

  if (response.status === 401 && !skipAuthRefresh) {
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
  return err instanceof ApiError ? err.message : fallback
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
