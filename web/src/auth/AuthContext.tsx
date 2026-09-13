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
  type LoginResult,
  type PasswordResetConfirmPayload,
  type RegisterResult,
  type TherapistRegisterPayload,
} from '@/api/auth'
import { ApiError } from '@/api/client'
import type { TherapistProfile, User } from '@/api/types'

interface AuthContextValue {
  user: User | null
  isLoading: boolean
  isAuthenticated: boolean
  login: (email: string, password: string) => Promise<LoginResult>
  loginMFA: (mfa_token: string, code: string) => Promise<void>
  loginWithGoogle: (credential: string) => Promise<void>
  register: (payload: TherapistRegisterPayload) => Promise<RegisterResult>
  verifyEmail: (email: string, code: string) => Promise<void>
  resendEmailCode: (email: string) => Promise<string>
  logout: () => Promise<void>
  refreshSession: () => Promise<void>
  requestPasswordReset: (email: string, recaptcha_token?: string) => Promise<string>
  verifyPasswordResetCode: (email: string, code: string) => Promise<string>
  confirmPasswordReset: (payload: PasswordResetConfirmPayload) => Promise<string>
}

const AuthContext = createContext<AuthContextValue | null>(null)

function profileToUser(profile: TherapistProfile): User {
  return {
    id: profile.id,
    email: profile.email,
    role: 'THERAPIST',
    first_name: profile.first_name,
    last_name: profile.last_name,
    avatar_url: profile.avatar_url,
  }
}

async function loadTherapistSession(): Promise<User> {
  const profile = await therapistApi.getProfile()
  return profileToUser(profile)
}

async function establishTherapistSession(
  setUser: (user: User) => void,
  nextUser: User,
): Promise<void> {
  if (nextUser.role !== 'THERAPIST') {
    await authApi.logout().catch(() => undefined)
    throw new ApiError(403, 'Panel webowy jest dostępny tylko dla fizjoterapeutów.')
  }
  try {
    setUser(await loadTherapistSession())
  } catch {
    setUser({ ...nextUser, avatar_url: nextUser.avatar_url ?? null })
  }
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    let cancelled = false

    async function restoreSession() {
      try {
        const nextUser = await loadTherapistSession()
        if (!cancelled) {
          setUser(nextUser)
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

  const login = useCallback(async (email: string, password: string): Promise<LoginResult> => {
    const result = await authApi.login(email, password)
    if (result.kind === 'authenticated') {
      await establishTherapistSession(setUser, result.user)
    }
    return result
  }, [])

  const loginMFA = useCallback(async (mfa_token: string, code: string) => {
    const { user: nextUser } = await authApi.loginMFA(mfa_token, code)
    await establishTherapistSession(setUser, nextUser)
  }, [])

  const loginWithGoogle = useCallback(async (credential: string) => {
    const { user: nextUser } = await authApi.loginWithGoogle(credential)
    await establishTherapistSession(setUser, nextUser)
  }, [])

  const register = useCallback(async (payload: TherapistRegisterPayload) => {
    const result = await authApi.registerTherapist(payload)
    if (result.kind === 'authenticated') {
      await establishTherapistSession(setUser, result.user)
    }
    return result
  }, [])

  const verifyEmail = useCallback(async (email: string, code: string) => {
    const { user: nextUser } = await authApi.verifyEmail(email, code)
    await establishTherapistSession(setUser, nextUser)
  }, [])

  const resendEmailCode = useCallback(async (email: string) => {
    const { detail } = await authApi.resendEmailCode(email)
    return detail
  }, [])

  const logout = useCallback(async () => {
    try {
      await authApi.logout()
    } finally {
      setUser(null)
    }
  }, [])

  const refreshSession = useCallback(async () => {
    const nextUser = await loadTherapistSession()
    setUser(nextUser)
  }, [])

  const requestPasswordReset = useCallback(async (email: string, recaptcha_token?: string) => {
    const { detail } = await authApi.requestPasswordReset(email, recaptcha_token)
    return detail
  }, [])

  const verifyPasswordResetCode = useCallback(async (email: string, code: string) => {
    const { reset_token } = await authApi.verifyPasswordResetCode(email, code)
    return reset_token
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
      loginMFA,
      loginWithGoogle,
      register,
      verifyEmail,
      resendEmailCode,
      logout,
      refreshSession,
      requestPasswordReset,
      verifyPasswordResetCode,
      confirmPasswordReset,
    }),
    [
      user,
      isLoading,
      login,
      loginMFA,
      loginWithGoogle,
      register,
      verifyEmail,
      resendEmailCode,
      logout,
      refreshSession,
      requestPasswordReset,
      verifyPasswordResetCode,
      confirmPasswordReset,
    ],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

// eslint-disable-next-line react-refresh/only-export-components
export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext)
  if (!ctx) {
    throw new Error('useAuth must be used within AuthProvider')
  }
  return ctx
}
