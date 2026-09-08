import { useEffect } from 'react'

import { useAuth } from '@/auth/AuthContext'

import { connectTherapistRealtime } from './sse'

/** Keeps one SSE connection for the authenticated therapist shell. */
export function useTherapistRealtimeConnection(): void {
  const { isAuthenticated, isLoading } = useAuth()

  useEffect(() => {
    if (isLoading || !isAuthenticated) {
      return
    }
    return connectTherapistRealtime()
  }, [isAuthenticated, isLoading])
}
