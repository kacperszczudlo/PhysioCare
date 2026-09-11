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
}

export type RegisterResult =
  | { kind: 'authenticated'; user: User }
  | { kind: 'needs_email_verification'; email: string; detail: string }

export interface PasswordResetConfirmPayload {
  reset_token: string
  new_password: string
  new_password_confirm: string
}

export const authApi = {
  login(email: string, password: string) {
    return api.post<AuthResponse>(
      '/auth/login/',
      { email, password, token_delivery: 'cookie' },
      { skipAuthRefresh: true },
    )
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
