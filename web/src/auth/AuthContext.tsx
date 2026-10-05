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
  type VerifyEmailResult,
} from '@/api/auth'
import { ApiError } from '@/api/client'
import type { TherapistProfile, User } from '@/api/types'

/** Zbiór właściwości i metod udostępnianych przez Kontekst Uwierzytelniania. */
interface AuthContextValue {
  /** Obiekt zalogowanego fizjoterapeuty lub null. */
  user: User | null
  /** Flaga informująca o trwającym przywracaniu sesji podczas inicjalizacji aplikacji. */
  isLoading: boolean
  /** Czy użytkownik jest obecnie zalogowany. */
  isAuthenticated: boolean
  /** Loguje użytkownika adresem e-mail i hasłem. */
  login: (email: string, password: string, recaptcha_token?: string) => Promise<LoginResult>
  /** Loguje użytkownika drugim składnikiem 2FA/TOTP. */
  loginMFA: (mfa_token: string, code: string) => Promise<void>
  /** Loguje użytkownika tokenem Google ID Token. */
  loginWithGoogle: (credential: string) => Promise<void>
  /** Rejestruje nowego fizjoterapeutę w systemie. */
  register: (payload: TherapistRegisterPayload) => Promise<RegisterResult>
  /** Weryfikuje kod z e-maila aktywujący nowe konto. */
  verifyEmail: (email: string, code: string) => Promise<VerifyEmailResult>
  /** Ponownie wysyła kod aktywacyjny na podany e-mail. */
  resendEmailCode: (email: string) => Promise<string>
  /** Wylogowuje fizjoterapeutę i czyści ciasteczka uwierzytelniające. */
  logout: () => Promise<void>
  /** Odświeża profil użytkownika i stan sesji. */
  refreshSession: () => Promise<void>
  /** Żąda wysłania kodu resetowania hasła na e-mail. */
  requestPasswordReset: (email: string, recaptcha_token?: string) => Promise<string>
  /** Weryfikuje 6-cyfrowy kod resetowania hasła. */
  verifyPasswordResetCode: (email: string, code: string) => Promise<string>
  /** Ustawia nowe hasło po pomyślnej weryfikacji tokena resetu. */
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

/**
 * Komponent dostawcy stanu uwierzytelniania w aplikacji webowej PhysioCare.
 *
 * Automatycznie weryfikuje ciasteczka sesji przy starcie aplikacji i udostępnia
 * kontekst stanu zalogowania oraz metody logowania/rejestracji w drzewie komponentów.
 */
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

  const login = useCallback(
    async (email: string, password: string, recaptcha_token?: string): Promise<LoginResult> => {
      const result = await authApi.login(email, password, recaptcha_token)
      if (result.kind === 'authenticated') {
        await establishTherapistSession(setUser, result.user)
      }
      return result
    },
    [],
  )

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

  const verifyEmail = useCallback(async (email: string, code: string): Promise<VerifyEmailResult> => {
    const result = await authApi.verifyEmail(email, code)
    if (result.kind === 'authenticated') {
      await establishTherapistSession(setUser, result.user)
    }
    return result
  }, [])

  const resendEmailCode = useCallback(async (email: string) => {
    const res = await authApi.resendEmailCode(email)
    return res.detail
  }, [])

  const logout = useCallback(async () => {
    try {
      await authApi.logout()
    } finally {
      setUser(null)
    }
  }, [])

  const refreshSession = useCallback(async () => {
    try {
      const nextUser = await loadTherapistSession()
      setUser(nextUser)
    } catch {
      setUser(null)
    }
  }, [])

  const requestPasswordReset = useCallback(async (email: string, recaptcha_token?: string) => {
    const res = await authApi.requestPasswordReset(email, recaptcha_token)
    return res.detail
  }, [])

  const verifyPasswordResetCode = useCallback(async (email: string, code: string) => {
    const res = await authApi.verifyPasswordResetCode(email, code)
    return res.reset_token
  }, [])

  const confirmPasswordReset = useCallback(async (payload: PasswordResetConfirmPayload) => {
    const res = await authApi.confirmPasswordReset(payload)
    return res.detail
  }, [])

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      isLoading,
      isAuthenticated: Boolean(user),
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

/**
 * Własny hook React uzyskujący dostęp do stanu i funkcji kontekstu uwierzytelniania.
 *
 * @returns Instancję AuthContextValue wewnątrz komponentów potomnych AuthProvider.
 * @throws {Error} Gdy hook zostanie wywołany poza drzewem AuthProvider.
 */
// eslint-disable-next-line react-refresh/only-export-components
export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext)
  if (!ctx) {
    throw new Error('useAuth must be used within AuthProvider')
  }
  return ctx
}
