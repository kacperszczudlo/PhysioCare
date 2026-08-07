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

export interface NetworkStatus {
  isOffline: boolean
  isResolved: boolean
  isConnected: boolean | null
  isInternetReachable: boolean | null
  refresh: () => Promise<void>
}

const NetworkContext = createContext<NetworkStatus | null>(null)

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

export function useNetwork(): NetworkStatus {
  const ctx = useContext(NetworkContext)
  if (!ctx) {
    throw new Error('useNetwork must be used within NetworkProvider')
  }
  return ctx
}

export function useNetworkOptional(): NetworkStatus | null {
  return useContext(NetworkContext)
}
