/**
 * @file sse.ts
 * @description Nawiązywanie i zarządzanie połączeniem Server-Sent Events (SSE) z serwerem API do obierania powiadomień w czasie rzeczywistym.
 */

import EventSource from 'react-native-sse'

import { API_BASE_URL, refreshAccessToken } from '@/api/client'
import { tokenStorage } from '@/api/tokenStorage'

import { realtimeBus } from './bus'
import { REALTIME_EVENT_TYPES, type RealtimeEvent, type RealtimeEventType } from './types'

const MIN_RETRY_MS = 1000
const MAX_RETRY_MS = 30_000
/** Android XHR często buforuje SSE - cykliczny timeout zmusza do odczytu bufora. */
const SSE_CYCLE_MS = 12_000

/** Generuje pełny adres URL punktu końcowego zdarzeń SSE */
function eventsUrl(): string {
  return `${API_BASE_URL.replace(/\/$/, '')}/me/events/`
}

/** Parsuje ciąg JSON z treścią zdarzenia SSE na obiekt `RealtimeEvent` */
function parsePayload(raw: string): RealtimeEvent | null {
  try {
    const data = JSON.parse(raw) as Partial<RealtimeEvent>
    if (typeof data.type !== 'string') {
      return null
    }
    return {
      type: data.type,
      resource_id: data.resource_id ?? null,
      at: typeof data.at === 'string' ? data.at : new Date().toISOString(),
    }
  } catch {
    return null
  }
}

/**
 * Nawiązuje połączenie Server-Sent Events (SSE) z serwerem dla zalogowanego pacjenta.
 * Obsługuje automatyczne ponawianie połączenia z wykładniczym opóźnieniem (exponential backoff) oraz odświeżaniem tokenów JWT.
 *
 * @returns Funkcja zamykająca strumień SSE i anulująca timery ponownych prób.
 */
export function connectPatientRealtime(): () => void {
  let closed = false
  let source: EventSource<RealtimeEventType> | null = null
  let retryTimer: ReturnType<typeof setTimeout> | null = null
  let retryDelay = MIN_RETRY_MS

  const clearRetry = () => {
    if (retryTimer != null) {
      clearTimeout(retryTimer)
      retryTimer = null
    }
  }

  const scheduleReconnect = () => {
    if (closed || retryTimer != null) {
      return
    }
    const delay = retryDelay
    retryDelay = Math.min(retryDelay * 2, MAX_RETRY_MS)
    retryTimer = setTimeout(() => {
      retryTimer = null
      void open()
    }, delay)
  }

  const tearDownSource = () => {
    if (!source) {
      return
    }
    try {
      source.removeAllEventListeners()
      source.close()
    } catch {
      // ignore
    }
    source = null
  }

  const open = async () => {
    if (closed) {
      return
    }
    clearRetry()
    tearDownSource()

    await refreshAccessToken()
    if (closed) {
      return
    }

    const access = await tokenStorage.getAccess()
    if (!access) {
      scheduleReconnect()
      return
    }

    const url = eventsUrl()
    const next = new EventSource<RealtimeEventType>(url, {
      headers: {
        Authorization: `Bearer ${access}`,
        Accept: 'text/event-stream',
      },
      debug: false,
      timeout: SSE_CYCLE_MS,
      pollingInterval: 1500,
      lineEndingCharacter: '\n',
    })
    source = next

    next.addEventListener('open', () => {
      retryDelay = MIN_RETRY_MS
      if (__DEV__) {
        console.info('[sse] connected', url)
      }
    })

    for (const type of REALTIME_EVENT_TYPES) {
      next.addEventListener(type, (message) => {
        if (!('data' in message) || typeof message.data !== 'string') {
          return
        }
        const event = parsePayload(message.data)
        if (!event || event.type === 'ping') {
          return
        }
        if (__DEV__) {
          console.info('[sse] event', event.type, event.resource_id)
        }
        realtimeBus.emit(event)
      })
    }

    next.addEventListener('error', (err) => {
      if (closed) {
        return
      }
      if (__DEV__) {
        console.warn('[sse] error', err)
      }
      if (err.type === 'timeout') {
        tearDownSource()
        retryDelay = MIN_RETRY_MS
        scheduleReconnect()
        return
      }
      if (err.type === 'error' && 'xhrStatus' in err && err.xhrStatus === 401) {
        tearDownSource()
        void refreshAccessToken().finally(scheduleReconnect)
        return
      }
      if (
        err.type === 'error' &&
        'xhrStatus' in err &&
        typeof err.xhrStatus === 'number' &&
        err.xhrStatus >= 400
      ) {
        tearDownSource()
        scheduleReconnect()
      }
    })
  }

  void open()

  return () => {
    closed = true
    clearRetry()
    tearDownSource()
  }
}
