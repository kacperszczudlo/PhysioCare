import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from 'react'

import { authApi, type PasswordResetConfirmPayload, type PatientRegisterPayload } from '@/api/auth'
import { ApiError, isNetworkFailure } from '@/api/client'
import { patientApi } from '@/api/patient'
import { tokenStorage } from '@/api/tokenStorage'
import type { User } from '@/api/types'
import { useNetworkOptional } from '@/network/NetworkContext'

interface AuthContextValue {
  user: User | null
  isLoading: boolean
  isAuthenticated: boolean
  login: (email: string, password: string) => Promise<void>
  register: (payload: PatientRegisterPayload) => Promise<void>
  logout: () => Promise<void>
  requestPasswordReset: (email: string) => Promise<string>
  confirmPasswordReset: (payload: PasswordResetConfirmPayload) => Promise<string>
}

const AuthContext = createContext<AuthContextValue | null>(null)

function profileToUser(profile: Awaited<ReturnType<typeof patientApi.getProfile>>): User {
  return {
    id: profile.id,
    email: profile.email,
    role: 'PATIENT',
    first_name: profile.first_name,
    last_name: profile.last_name,
  }
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const network = useNetworkOptional()
  const wasOffline = useRef(false)
  const userRef = useRef<User | null>(null)
  userRef.current = user

  const hydrateFromProfile = useCallback(async (): Promise<void> => {
    const access = await tokenStorage.getAccess()
    if (!access) {
      setUser(null)
      return
    }

    try {
      const profile = await patientApi.getProfile()
      const next = profileToUser(profile)
      setUser(next)
      await tokenStorage.setCachedUser(next)
    } catch (error) {
      if (error instanceof ApiError && (error.status === 401 || error.status === 403)) {
        setUser(null)
        await tokenStorage.clear()
        return
      }

      if (!isNetworkFailure(error)) {
        console.error('Session restore failed', error)
      }

      // Keep existing in-memory user if present; otherwise fall back to cache.
      if (!userRef.current) {
        const cached = await tokenStorage.getCachedUser()
        setUser(cached)
      }
    }
  }, [])

  useEffect(() => {
    let cancelled = false

    async function restoreSession() {
      try {
        await hydrateFromProfile()
      } catch (error) {
        if (!cancelled) {
          console.error('Session restore failed', error)
          setUser(null)
        }
      } finally {
        if (!cancelled) {
          setIsLoading(false)
        }
      }
    }

    void restoreSession()
    return () => {
      cancelled = true
    }
  }, [hydrateFromProfile])

  // When connectivity returns, refresh profile if we still have tokens.
  useEffect(() => {
    if (!network?.isResolved) {
      return
    }

    if (network.isOffline) {
      wasOffline.current = true
      return
    }

    if (!wasOffline.current) {
      return
    }
    wasOffline.current = false

    void (async () => {
      const access = await tokenStorage.getAccess()
      if (!access) {
        return
      }
      try {
        const profile = await patientApi.getProfile()
        const next = profileToUser(profile)
        setUser(next)
        await tokenStorage.setCachedUser(next)
      } catch (error) {
        if (error instanceof ApiError && (error.status === 401 || error.status === 403)) {
          setUser(null)
          await tokenStorage.clear()
        }
      }
    })()
  }, [network?.isOffline, network?.isResolved])

  const login = useCallback(async (email: string, password: string) => {
    const nextUser = await authApi.login(email, password)
    if (nextUser.role !== 'PATIENT') {
      await authApi.logout().catch(() => undefined)
      throw new ApiError(403, 'Aplikacja mobilna jest dostępna tylko dla pacjentów.')
    }
    setUser(nextUser)
    await tokenStorage.setCachedUser(nextUser)
  }, [])

  const register = useCallback(async (payload: PatientRegisterPayload) => {
    const nextUser = await authApi.registerPatient(payload)
    setUser(nextUser)
    await tokenStorage.setCachedUser(nextUser)
  }, [])

  const logout = useCallback(async () => {
    try {
      await authApi.logout()
    } finally {
      setUser(null)
    }
  }, [])

  const requestPasswordReset = useCallback(async (email: string) => {
    const { detail } = await authApi.requestPasswordReset(email)
    return detail
  }, [])

  const confirmPasswordReset = useCallback(async (payload: PasswordResetConfirmPayload) => {
    const { detail } = await authApi.confirmPasswordReset(payload)
    return detail
  }, [])

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      isLoading,
      isAuthenticated: user !== null,
      login,
      register,
      logout,
      requestPasswordReset,
      confirmPasswordReset,
    }),
    [user, isLoading, login, register, logout, requestPasswordReset, confirmPasswordReset],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext)
  if (!ctx) {
    throw new Error('useAuth must be used within AuthProvider')
  }
  return ctx
}
