import { api } from './client'
import type {
  CompetenceSnapshot,
  DashboardStats,
  QualificationLevel,
  TherapistProfile,
  User,
} from './types'

/** Odpowiedź uwierzytelniania zawierająca instancję zalogowanego użytkownika. */
interface AuthResponse {
  user: User
}

/** Payload danych wymaganych przy rejestracji fizjoterapeuty. */
export interface TherapistRegisterPayload {
  /** Adres e-mail użytkownika. */
  email?: string
  /** Hasło konta. */
  password?: string
  /** Opcjonalny token Google ID Token (rejestracja przez Google). */
  google_credential?: string
  /** Token reCAPTCHA v2/v3 do weryfikacji antybotowej. */
  recaptcha_token?: string
  /** Imię fizjoterapeuty. */
  first_name?: string
  /** Nazwisko fizjoterapeuty. */
  last_name?: string
  /** Numer Prawa Wykonywania Zawodu Fizjoterapeuty (5 cyfr). */
  pwzf_number: string
  /** Obowiązkowe oświadczenie o posiadaniu aktywnych uprawnień PWZF. */
  pwzf_declaration: boolean
  /** Numer telefonu kontaktowego. */
  phone?: string
  /** Poziom kwalifikacji zawodowych. */
  qualification_level?: QualificationLevel
}

/** Wynik operacji rejestracji – zalogowany lub oczekujący na kod z e-maila. */
export type RegisterResult =
  | { kind: 'authenticated'; user: User }
  | { kind: 'needs_email_verification'; email: string; detail: string }

/** Payload potwierdzenia resetu hasła nowym hasłem. */
export interface PasswordResetConfirmPayload {
  /** Jednorazowy token zweryfikowanego resetu hasła. */
  reset_token: string
  /** Nowe hasło spełniające wymogi polityki haseł. */
  new_password: string
  /** Powtórzenie nowego hasła. */
  new_password_confirm: string
}

/** Wynik logowania – zrealizowane lub wymagające weryfikacji składnika 2FA. */
export type LoginResult =
  { kind: 'authenticated'; user: User } | { kind: 'mfa_required'; mfa_token: string; email: string }

/** Odpowiedź z danymi konfiguracyjnymi uwierzytelniania dwuskładnikowego 2FA/TOTP. */
export interface MFASetupResponse {
  /** Tajny klucz TOTP w formacie Base32. */
  secret_key: string
  /** URL otpauth do zeskanowania w aplikacji Google Authenticator / Authy. */
  otpauth_url: string
  /** Kod SVG z obrazem kodu QR do skanowania. */
  qr_code_svg: string
}

/** Odpowiedź po pomyślnym włączeniu 2FA wraz z kodami zapasowymi. */
export interface MFAEnableResponse {
  /** Komunikat sukcesu z backendu. */
  message: string
  /** Jednorazowe kody ratunkowe/zapasowe (backup codes). */
  backup_codes: string[]
}

/** Status włączenia i wymogu 2FA dla wybranej roli. */
export interface MFAStatusResponse {
  /** Czy użytkownik ma obecnie aktywne 2FA. */
  is_enabled: boolean
  /** Czy 2FA jest obowiązkowe dla roli danego użytkownika. */
  mfa_required_for_role: boolean
}

/** Usługi API uwierzytelniania, rejestracji, resetu hasła oraz 2FA/MFA. */
export const authApi = {
  async login(email: string, password: string, recaptcha_token?: string): Promise<LoginResult> {
    const data = await api.post<
      AuthResponse | { mfa_required?: boolean; mfa_token?: string; email?: string }
    >(
      '/auth/login/',
      { email, password, recaptcha_token, token_delivery: 'cookie' },
      { skipAuthRefresh: true },
    )
    if (data && 'mfa_required' in data && data.mfa_required) {
      return {
        kind: 'mfa_required',
        mfa_token: typeof data.mfa_token === 'string' ? data.mfa_token : '',
        email: typeof data.email === 'string' ? data.email : email,
      }
    }
    if (data && 'user' in data && data.user) {
      return { kind: 'authenticated', user: data.user }
    }
    throw new Error('Nieoczekiwana odpowiedź logowania.')
  },

  loginMFA(mfa_token: string, code: string) {
    return api.post<AuthResponse>(
      '/auth/2fa/login/',
      { mfa_token, code, token_delivery: 'cookie' },
      { skipAuthRefresh: true },
    )
  },

  setupMFA() {
    return api.post<MFASetupResponse>('/auth/2fa/setup/')
  },

  enableMFA(code: string) {
    return api.post<MFAEnableResponse>('/auth/2fa/enable/', { code })
  },

  disableMFA(password: string, code?: string) {
    return api.post<{ message: string }>('/auth/2fa/disable/', { password, code })
  },

  getMFAStatus() {
    return api.get<MFAStatusResponse>('/auth/2fa/status/')
  },

  loginWithGoogle(credential: string) {
    return api.post<AuthResponse>(
      '/auth/google/',
      { credential, token_delivery: 'cookie' },
      { skipAuthRefresh: true },
    )
  },

  async registerTherapist(payload: TherapistRegisterPayload): Promise<RegisterResult> {
    const data = await api.post<
      | AuthResponse
      | {
          needs_email_verification?: boolean
          email?: string
          detail?: string
        }
    >(
      '/auth/register/therapist/',
      { ...payload, token_delivery: 'cookie' },
      { skipAuthRefresh: true },
    )
    if (data && 'needs_email_verification' in data && data.needs_email_verification) {
      return {
        kind: 'needs_email_verification',
        email: typeof data.email === 'string' ? data.email : '',
        detail: typeof data.detail === 'string' ? data.detail : 'Sprawdź e-mail i wpisz kod.',
      }
    }
    if (data && 'user' in data && data.user) {
      return { kind: 'authenticated', user: data.user }
    }
    throw new Error('Nieoczekiwana odpowiedź rejestracji.')
  },

  verifyEmail(email: string, code: string) {
    return api.post<AuthResponse>(
      '/auth/email/verify/',
      { email, code, token_delivery: 'cookie' },
      { skipAuthRefresh: true },
    )
  },

  resendEmailCode(email: string) {
    return api.post<{ detail: string }>('/auth/email/resend/', { email }, { skipAuthRefresh: true })
  },

  requestPasswordReset(email: string, recaptcha_token?: string) {
    return api.post<{ detail: string }>(
      '/auth/password-reset/request/',
      { email, client: 'web', recaptcha_token },
      { skipAuthRefresh: true },
    )
  },

  verifyPasswordResetCode(email: string, code: string) {
    return api.post<{ detail: string; reset_token: string }>(
      '/auth/password-reset/verify/',
      { email, code },
      { skipAuthRefresh: true },
    )
  },

  confirmPasswordReset(payload: PasswordResetConfirmPayload) {
    return api.post<{ detail: string }>('/auth/password-reset/confirm/', payload, {
      skipAuthRefresh: true,
    })
  },

  logout() {
    return api.post<{ detail: string }>('/auth/logout/', {}, { skipAuthRefresh: true })
  },

  changePassword(current_password: string, new_password: string) {
    return api.post<{ detail: string }>('/auth/password-change/', {
      current_password,
      new_password,
    })
  },
}

export interface TherapistProfileUpdatePayload {
  first_name?: string
  last_name?: string
  phone?: string
  location_address?: string
  bio?: string
  courses?: string[]
  qualification_level?: QualificationLevel
  experience_years?: number
}

export const therapistApi = {
  getProfile() {
    return api.get<TherapistProfile>('/therapist/profile/')
  },

  updateProfile(payload: TherapistProfileUpdatePayload) {
    return api.patch<TherapistProfile>('/therapist/profile/', payload)
  },

  getCompetences() {
    return api.get<CompetenceSnapshot>('/therapist/competences/')
  },

  uploadAvatar(file: File) {
    const body = new FormData()
    body.append('file', file)
    return api.post<TherapistProfile>('/therapist/profile/avatar/', body)
  },

  getDashboardStats() {
    return api.get<DashboardStats>('/therapist/dashboard/stats/')
  },
}
