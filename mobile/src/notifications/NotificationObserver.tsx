/**
 * @file NotificationObserver.tsx
 * @description Niewidoczny komponent obserwatora powiadomień Push (NotificationObserver) odpowiadający za automatyczną rejestrację tokena po zalogowaniu oraz obsługę przekierowań nawigacyjnych po kliknięciu powiadomienia.
 */

import { useRouter } from 'expo-router'
import { useEffect, useRef } from 'react'

import { useAuth } from '@/auth/AuthContext'
import {
  isRemotePushSupported,
  openFromNotificationData,
  registerAndUploadPushToken,
  subscribeNotificationResponses,
} from '@/notifications/push'

/**
 * Komponent obserwatora powiadomień systemowych w tle.
 *
 * @returns Komponent nie renderujący żadnego widoku (zwraca null).
 */
export function NotificationObserver() {
  const { isAuthenticated, isLoading } = useAuth()
  const router = useRouter()
  const handledPayload = useRef<string | null>(null)

  useEffect(() => {
    if (!isAuthenticated || isLoading || !isRemotePushSupported()) {
      return
    }
    void registerAndUploadPushToken()
  }, [isAuthenticated, isLoading])

  useEffect(() => {
    if (!isAuthenticated || !isRemotePushSupported()) {
      return
    }

    let cancelled = false
    let unsubscribe: (() => void) | undefined

    void subscribeNotificationResponses((data) => {
      const key = JSON.stringify(data ?? {})
      if (handledPayload.current === key) {
        return
      }
      handledPayload.current = key
      openFromNotificationData(router, data)
    }).then((fn) => {
      if (cancelled) {
        fn()
        return
      }
      unsubscribe = fn
    })

    return () => {
      cancelled = true
      unsubscribe?.()
    }
  }, [isAuthenticated, router])

  return null
}

