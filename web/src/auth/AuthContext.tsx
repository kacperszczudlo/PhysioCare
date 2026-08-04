import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react'

import {
  authApi,
  therapistApi,
  type PasswordResetConfirmPayload,
  type TherapistRegisterPayload,
} from '@/api/auth'
import { ApiError } from '@/api/client'
import type { User } from '@/api/types'

interface AuthContextValue {
  user: User | null
  isLoading: boolean
  isAuthenticated: boolean
  login: (email: string, password: string) => Promise<void>
  register: (payload: TherapistRegisterPayload) => Promise<void>
  logout: () => Promise<void>
  requestPasswordReset: (email: string) => Promise<string>
  confirmPasswordReset: (payload: PasswordResetConfirmPayload) => Promise<string>
}

const AuthContext = createContext<AuthContextValue | null>(null)

function profileToUser(profile: Awaited<ReturnType<typeof therapistApi.getProfile>>): User {
  return {
    id: profile.id,
    email: profile.email,
    role: 'THERAPIST',
    first_name: profile.first_name,
    last_name: profile.last_name,
  }
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    let cancelled = false

    async function restoreSession() {
      try {
        const profile = await therapistApi.getProfile()
        if (!cancelled) {
          setUser(profileToUser(profile))
        }
      } catch (error) {
        if (!cancelled) {
          setUser(null)
          if (!(error instanceof ApiError && (error.status === 401 || error.status === 403))) {
            console.error('Session restore failed', error)
          }
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
  }, [])

  const login = useCallback(async (email: string, password: string) => {
    const { user: nextUser } = await authApi.login(email, password)
    if (nextUser.role !== 'THERAPIST') {
      await authApi.logout().catch(() => undefined)
      throw new ApiError(403, 'Panel webowy jest dostępny tylko dla fizjoterapeutów.')
    }
    setUser(nextUser)
  }, [])

  const register = useCallback(async (payload: TherapistRegisterPayload) => {
    const { user: nextUser } = await authApi.registerTherapist(payload)
    setUser(nextUser)
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
    [
      user,
      isLoading,
      login,
      register,
      logout,
      requestPasswordReset,
      confirmPasswordReset,
    ],
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
