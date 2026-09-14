import { API_BASE_URL, refreshAccessToken } from '@/api/client'

import { realtimeBus } from './bus'
import { REALTIME_EVENT_TYPES, type RealtimeEvent } from './types'

const MIN_RETRY_MS = 1000
const MAX_RETRY_MS = 30_000
const EXPONENTIAL_BACKOFF_FACTOR = 2
const DEV_DJANGO_PORT = 8000

/**
 * W DEV EventSource idzie prosto na Django (:8000), omijając proxy Vite -
 * http-proxy często buforuje SSE i UI „nie żyje”.
 * Cookies JWT są host-only dla localhost (port nieistotny).
 */
function eventsUrl(): string {
  if (import.meta.env.DEV && API_BASE_URL.startsWith('/')) {
    return `http://localhost:${DEV_DJANGO_PORT}/api/v1/me/events/`
  }
  const base = API_BASE_URL.replace(/\/$/, '')
  return `${base}/me/events/`
}

function parseEvent(raw: string): RealtimeEvent | null {
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

/** Opens SSE to `/me/events/`. Returns disposer. Cookie auth (withCredentials). */
export function connectTherapistRealtime(): () => void {
  let closed = false
  let source: EventSource | null = null
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
    retryDelay = Math.min(retryDelay * EXPONENTIAL_BACKOFF_FACTOR, MAX_RETRY_MS)
    retryTimer = setTimeout(() => {
      retryTimer = null
      void open()
    }, delay)
  }

  const open = async () => {
    if (closed) {
      return
    }
    clearRetry()
    source?.close()
    source = null

    await refreshAccessToken()

    if (closed) {
      return
    }

    const url = eventsUrl()
    const next = new EventSource(url, { withCredentials: true })
    source = next

    next.onopen = () => {
      retryDelay = MIN_RETRY_MS
      if (import.meta.env.DEV) {
        console.info('[sse] connected', url)
      }
    }

    for (const type of REALTIME_EVENT_TYPES) {
      next.addEventListener(type, (message) => {
        if (!(message instanceof MessageEvent) || typeof message.data !== 'string') {
          return
        }
        const event = parseEvent(message.data)
        if (!event || event.type === 'ping') {
          return
        }
        if (import.meta.env.DEV) {
          console.info('[sse] event', event.type, event.resource_id)
        }
        realtimeBus.emit(event)
      })
    }

    next.onerror = () => {
      if (import.meta.env.DEV) {
        console.warn('[sse] error/reconnect', url)
      }
      next.close()
      if (source === next) {
        source = null
      }
      scheduleReconnect()
    }
  }

  void open()

  return () => {
    closed = true
    clearRetry()
    source?.close()
    source = null
  }
}
