import { useRouter } from 'expo-router'
import { useEffect, useRef } from 'react'

import { useAuth } from '@/auth/AuthContext'
import {
  isRemotePushSupported,
  openFromNotificationData,
  registerAndUploadPushToken,
  subscribeNotificationResponses,
} from '@/notifications/push'

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
