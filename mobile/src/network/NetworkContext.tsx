/**
 * @file NetworkContext.tsx
 * @description Kontekst monitorowania stanu sieci (NetInfo) w czasie rzeczywistym z automatyczną detekcją braku internetu (offline).
 */

import NetInfo, { type NetInfoState } from '@react-native-community/netinfo'
import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react'

/**
 * Stan połączenia sieciowego urządzenia.
 */
export interface NetworkStatus {
  /** Czy urządzenie jest obecnie w trybie offline (brak połączenia lub nieosiągalny internet) */
  isOffline: boolean
  /** Czy pierwszy stan po inicjalizacji został już ustalony */
  isResolved: boolean
  /** Flaga połaczenia z fizycznym interfejsem sieciowym (WiFi/Cellular) */
  isConnected: boolean | null
  /** Flaga rzeczywistej dostępności sieci internetowej */
  isInternetReachable: boolean | null
  /** Ręczne odświeżenie statusu sieci */
  refresh: () => Promise<void>
}

const NetworkContext = createContext<NetworkStatus | null>(null)

/** Określa, czy na podstawie stanu NetInfo urządzenie znajduje się w stanie offline */
function deriveOffline(state: NetInfoState | null): boolean {
  if (!state) {
    return false
  }
  if (state.isConnected === false) {
    return true
  }
  if (state.isInternetReachable === false) {
    return true
  }
  return false
}

/**
 * Dostawca kontekstu sieciowego (NetworkProvider) nasłuchujący zdarzeń zmiany stanu łączności z internetem.
 *
 * @param props - Komponenty potomne (`children`).
 */
export function NetworkProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<NetInfoState | null>(null)
  const [isResolved, setIsResolved] = useState(false)

  useEffect(() => {
    let mounted = true

    void NetInfo.fetch().then((next) => {
      if (!mounted) {
        return
      }
      setState(next)
      setIsResolved(true)
    })

    const unsubscribe = NetInfo.addEventListener((next) => {
      setState(next)
      setIsResolved(true)
    })

    return () => {
      mounted = false
      unsubscribe()
    }
  }, [])

  const refresh = useCallback(async () => {
    const next = await NetInfo.fetch()
    setState(next)
    setIsResolved(true)
  }, [])

  const value = useMemo<NetworkStatus>(
    () => ({
      isOffline: deriveOffline(state),
      isResolved,
      isConnected: state?.isConnected ?? null,
      isInternetReachable: state?.isInternetReachable ?? null,
      refresh,
    }),
    [state, isResolved, refresh],
  )

  return <NetworkContext.Provider value={value}>{children}</NetworkContext.Provider>
}

/**
 * Wymagany hook dający dostęp do bieżącego stanu łączności sieciowej.
 *
 * @returns Instancja `NetworkStatus`.
 */
export function useNetwork(): NetworkStatus {
  const ctx = useContext(NetworkContext)
  if (!ctx) {
    throw new Error('useNetwork must be used within NetworkProvider')
  }
  return ctx
}

/**
 * Opcjonalny hook dający dostęp do kontekstu sieci (zwraca null w przypadku użycia poza dostawcą).
 *
 * @returns Instancja `NetworkStatus` lub null.
 */
export function useNetworkOptional(): NetworkStatus | null {
  return useContext(NetworkContext)
}
