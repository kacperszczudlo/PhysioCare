import { useEffect, useRef } from 'react'
import { AppState, type AppStateStatus } from 'react-native'

import { useAuth } from '@/auth/AuthContext'

import { connectPatientRealtime } from './sse'

/** One SSE connection while the patient is authenticated and app is active. */
export function RealtimeObserver() {
  const { isAuthenticated, isLoading } = useAuth()
  const disposeRef = useRef<(() => void) | null>(null)

  useEffect(() => {
    if (isLoading || !isAuthenticated) {
      disposeRef.current?.()
      disposeRef.current = null
      return
    }

    const start = () => {
      disposeRef.current?.()
      disposeRef.current = connectPatientRealtime()
    }

    const stop = () => {
      disposeRef.current?.()
      disposeRef.current = null
    }

    if (AppState.currentState === 'active') {
      start()
    }

    const onAppState = (next: AppStateStatus) => {
      if (next === 'active') {
        start()
      } else {
        stop()
      }
    }

    const sub = AppState.addEventListener('change', onAppState)
    return () => {
      sub.remove()
      stop()
    }
  }, [isAuthenticated, isLoading])

  return null
}
