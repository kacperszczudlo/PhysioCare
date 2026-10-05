/**
 * @file OfflineSyncObserver.tsx
 * @description Niewidoczny obserwator automatycznej synchronizacji kolejki offline (OfflineSyncObserver).
 * Uruchamia synchronizację zaległych operacji po powrocie łączności internetowej lub wznowieniu aplikacji.
 */

import { useCallback, useEffect, useRef } from 'react'
import { AppState, type AppStateStatus } from 'react-native'

import { useAuth } from '@/auth/AuthContext'
import { useToast } from '@/components/ToastContext'
import { useNetwork } from '@/network/NetworkContext'
import { flushOfflineQueue } from './offlineQueue'

export function OfflineSyncObserver() {
  const { isOffline, isResolved } = useNetwork()
  const { isAuthenticated, isLoading } = useAuth()
  const { toast } = useToast()
  const wasOffline = useRef(false)
  const isSyncing = useRef(false)

  const sync = useCallback(async () => {
    if (isSyncing.current || isOffline || !isAuthenticated) {
      return
    }
    isSyncing.current = true
    try {
      const { synced } = await flushOfflineQueue()
      if (synced > 0) {
        toast.success(
          'Synchronizacja offline',
          synced === 1
            ? 'Zsynchronizowano 1 zaległe ćwiczenie z serwerem.'
            : `Zsynchronizowano zaległe ćwiczenia (${synced}) z serwerem.`,
        )
      }
    } catch (err) {
      console.warn('Błąd synchronizacji kolejki offline:', err)
    } finally {
      isSyncing.current = false
    }
  }, [isOffline, isAuthenticated, toast])

  // Nasłuchuj powrotu sieci (przejście z offline do online)
  useEffect(() => {
    if (!isResolved || isLoading || !isAuthenticated) {
      return
    }

    if (isOffline) {
      wasOffline.current = true
      return
    }

    if (wasOffline.current) {
      wasOffline.current = false
      void sync()
    }
  }, [isOffline, isResolved, isLoading, isAuthenticated, sync])

  // Synchronizuj również przy starcie i przejściu aplikacji na pierwszy plan
  useEffect(() => {
    if (isLoading || !isAuthenticated || isOffline) {
      return
    }

    // Sprawdź kolejkę przy montowaniu
    void sync()

    const onAppState = (next: AppStateStatus) => {
      if (next === 'active' && !isOffline) {
        void sync()
      }
    }

    const sub = AppState.addEventListener('change', onAppState)
    return () => {
      sub.remove()
    }
  }, [isLoading, isAuthenticated, isOffline, sync])

  return null
}
