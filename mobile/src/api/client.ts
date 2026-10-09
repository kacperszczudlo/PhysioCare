/**
 * @file client.ts
 * @description Główny klient HTTP aplikacji mobilnej z automatyczną obsługą tokenów JWT, odświeżaniem sesji, detekcją braku sieci oraz przekroczenia czasu żądania.
 */

import { HTTP_STATUS } from './httpStatus'
import type { ApiErrorBody } from './types'
import { tokenStorage } from './tokenStorage'
import { rewriteLocalhostToLan } from '@/lib/lanHost'

const configured = (process.env.EXPO_PUBLIC_API_BASE_URL ?? '').replace(/\/$/, '')
const rawBase = configured.length > 0 ? configured : 'http://localhost:8000/api/v1'

/** Bazowy adres URL interfejsu API z uwzględnieniem mapowania lokalnego hosta na sieć LAN */
export const API_BASE_URL = rewriteLocalhostToLan(rawBase)

/**
 * Klasa błędu reprezentująca błąd zwrócony przez serwer REST API (status HTTP 4xx / 5xx).
 */
export class ApiError extends Error {
  /** Kod statusu odpowiedź HTTP (np. 400, 401, 404, 500) */
  readonly status: number
  /** Unikalny kod błędu dostarczony przez API (np. VALIDATION_ERROR) */
  readonly code: string
  /** Szczegółowe błędy przypisane do poszczególnych pól formularza */
  readonly details: Record<string, unknown>
  /** Surowe ciało odpowiedzi błędu z serwera */
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

/**
 * Klasa błędu reprezentująca awarię połączenia sieciowego lub braku dostępności serwera.
 */
export class NetworkError extends Error {
  /** Przyczyna awarii: 'offline' (brak sieci na urządzeniu) lub 'unreachable' (nieosiągalny serwer) */
  readonly reason: 'offline' | 'unreachable'

  constructor(reason: 'offline' | 'unreachable', message: string) {
    super(message)
    this.name = 'NetworkError'
    this.reason = reason
  }
}

/**
 * Sprawdza, czy podany błąd jest błędem sieciowym (brak internetu lub brak odpowiedzi serwera).
 *
 * @param err - Obiekt przechwyconego błędu.
 * @returns True jeśli błąd wynika z braku łączności.
 */
export function isNetworkFailure(err: unknown): boolean {
  return err instanceof NetworkError || err instanceof TypeError
}

/** Opcje konfiguracji pojedynczego żądania HTTP */
type RequestOptions = Omit<RequestInit, 'body'> & {
  /** Ciało żądania (dowolny obiekt JSON lub FormData) */
  body?: unknown
  /** Czy pominąć automatyczną próbę odświeżenia tokena przy kodzie 401 */
  skipAuthRefresh?: boolean
  /** Czy dołączyć nagłówek Authorization Bearer (domyślnie true) */
  auth?: boolean
}

/** Limit czasu oczekiwania na odpowiedź HTTP w milisekundach (30s z uwagi na cold-start darmowych instancji chmurowych) */
const REQUEST_TIMEOUT_MS = 30000

let refreshPromise: Promise<boolean> | null = null

/**
 * Wykonuje zapytanie HTTP fetch z twardym limitem czasu (timeout).
 */
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

/**
 * Wyciąga pierwszą czytelną wiadomość walidacyjną z ciała błędu API.
 */
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

/**
 * Generuje czytelny komunikat błędu po polsku na podstawie statusu HTTP i ciała odpowiedzi.
 */
function parseErrorMessage(status: number, body: ApiErrorBody | null): string {
  const fromBody = firstValidationMessage(body)
  if (fromBody) {
    return fromBody
  }
  if (status === HTTP_STATUS.UNAUTHORIZED) {
    return 'Sesja wygasła. Zaloguj się ponownie.'
  }
  if (status === HTTP_STATUS.FORBIDDEN) {
    return 'Brak uprawnień do tego zasobu.'
  }
  if (status === HTTP_STATUS.NOT_FOUND) {
    return 'Nie znaleziono zasobu.'
  }
  if (status === HTTP_STATUS.CONFLICT) {
    return 'Konflikt danych (np. kolizja terminu).'
  }
  if (status >= HTTP_STATUS.INTERNAL_SERVER_ERROR) {
    return 'Błąd serwera. Spróbuj ponownie później.'
  }
  return 'Wystąpił nieoczekiwany błąd.'
}

/**
 * Parsuje ciało odpowiedzi jako obiekt JSON, zwracając null w przypadku pustej odpowiedzi lub błędu składni.
 */
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

/** Zwraca domyślny komunikat o braku połączenia internetowego */
function offlineMessage(): string {
  return 'Brak połączenia z internetem. Sprawdź sieć i spróbuj ponownie.'
}

/** Zwraca komunikat o braku możliwości nawiązania połączenia z serwerem API */
function unreachableMessage(): string {
  if (__DEV__) {
    return `Nie udało się połączyć z API (${API_BASE_URL}). Na telefonie ustaw EXPO_PUBLIC_API_BASE_URL na IP komputera, nie localhost.`
  }
  return 'Nie udało się połączyć z serwerem. Sprawdź połączenie internetowe i spróbuj ponownie.'
}

/** Sprawdza status dostępności sieci na urządzeniu mobilnym */
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

/** Mapuje wyłapany wyjątek na odpowiedni obiekt NetworkError */
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

/** Próbuje odświeżyć token sesji JWT za pomocą tokena refresh */
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

/**
 * Odświeża access token JWT (np. przed połączeniem SSE lub po wygaśnięciu sesji).
 *
 * @returns Promise<boolean> - True, jeśli token został pomyślnie odświeżony.
 */
export async function refreshAccessToken(): Promise<boolean> {
  return tryRefreshSession()
}

/**
 * Wykonuje niskopoziomowe zapytanie HTTP do serwera API z obsługą tokenów i błędów.
 *
 * @template T - Oczekiwany typ zwracanych danych JSON.
 * @param path - Ścieżka końcowa (endpoint) lub pełny URL.
 * @param options - Opcje konfiguracyjne żądania HTTP.
 * @returns Zwraca obietnicę zawierającą odpowiedź typu T.
 */
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

  if (response.status === HTTP_STATUS.UNAUTHORIZED && auth && !skipAuthRefresh) {
    const refreshed = await tryRefreshSession()
    if (refreshed) {
      return apiRequest<T>(path, { ...options, skipAuthRefresh: true })
    }
  }

  if (response.status === HTTP_STATUS.NO_CONTENT) {
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

/**
 * Zwraca czytelny komunikat błędu na podstawie zgłoszonego wyjątku.
 *
 * @param err - Obiekt błędu.
 * @param fallback - Domyślna wiadomość awaryjna.
 * @returns Wiadomość błędu po polsku.
 */
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

/**
 * Pobiera komunikat błędu przypisany do konkretnego pola formularza z błędu API.
 *
 * @param err - Przechwycony błąd.
 * @param field - Nazwa pola (np. 'email', 'phone').
 * @returns Tekst błędu walidacji lub null.
 */
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

/**
 * Pomocniczy obiekt z wygodnymi metodami HTTP (get, post, patch, put, delete).
 */
export const api = {
  /** Wykonuje zapytanie GET */
  get: <T>(path: string, options?: RequestOptions) =>
    apiRequest<T>(path, { ...options, method: 'GET' }),

  /** Wykonuje zapytanie POST */
  post: <T>(path: string, body?: unknown, options?: RequestOptions) =>
    apiRequest<T>(path, { ...options, method: 'POST', body }),

  /** Wykonuje zapytanie PATCH */
  patch: <T>(path: string, body?: unknown, options?: RequestOptions) =>
    apiRequest<T>(path, { ...options, method: 'PATCH', body }),

  /** Wykonuje zapytanie PUT */
  put: <T>(path: string, body?: unknown, options?: RequestOptions) =>
    apiRequest<T>(path, { ...options, method: 'PUT', body }),

  /** Wykonuje zapytanie DELETE */
  delete: <T>(path: string, options?: RequestOptions) =>
    apiRequest<T>(path, { ...options, method: 'DELETE' }),
}
