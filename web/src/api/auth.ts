import { api } from './client'
import type {
  CompetenceSnapshot,
  DashboardStats,
  QualificationLevel,
  TherapistProfile,
  User,
} from './types'

interface AuthResponse {
  user: User
}

export interface TherapistRegisterPayload {
  email?: string
  password?: string
  google_credential?: string
  recaptcha_token?: string
  first_name?: string
  last_name?: string
  pwzf_number: string
  pwzf_declaration: boolean
  phone?: string
  qualification_level?: QualificationLevel
}

export type RegisterResult =
  | { kind: 'authenticated'; user: User }
  | { kind: 'needs_email_verification'; email: string; detail: string }

export interface PasswordResetConfirmPayload {
  reset_token: string
  new_password: string
  new_password_confirm: string
}

export type LoginResult =
  { kind: 'authenticated'; user: User } | { kind: 'mfa_required'; mfa_token: string; email: string }

export interface MFASetupResponse {
  secret_key: string
  otpauth_url: string
  qr_code_svg: string
}

export interface MFAEnableResponse {
  message: string
  backup_codes: string[]
}

export interface MFAStatusResponse {
  is_enabled: boolean
  mfa_required_for_role: boolean
}

export const authApi = {
  async login(email: string, password: string): Promise<LoginResult> {
    const data = await api.post<
      AuthResponse | { mfa_required?: boolean; mfa_token?: string; email?: string }
    >('/auth/login/', { email, password, token_delivery: 'cookie' }, { skipAuthRefresh: true })
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
