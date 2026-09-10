import { api } from './client'
import { tokenStorage } from './tokenStorage'
import type { AuthResponse, User } from './types'

export interface PatientRegisterPayload {
  email?: string
  password?: string
  google_credential?: string
  first_name?: string
  last_name?: string
  therapist_id: string
  phone?: string
  consents: {
    terms: boolean
    medical_data: boolean
  }
}

export type RegisterResult =
  | { kind: 'authenticated'; user: User }
  | { kind: 'needs_email_verification'; email: string; detail: string }

export interface PasswordResetConfirmPayload {
  reset_token: string
  new_password: string
  new_password_confirm: string
}

async function persistAuth(response: AuthResponse): Promise<User> {
  await tokenStorage.setTokens(response.access, response.refresh)
  return response.user
}

export const authApi = {
  async login(email: string, password: string) {
    const data = await api.post<AuthResponse>(
      '/auth/login/',
      { email, password },
      { auth: false, skipAuthRefresh: true },
    )
    return persistAuth(data)
  },

  async loginWithGoogle(credential: string) {
    const data = await api.post<AuthResponse>(
      '/auth/google/',
      { credential },
      { auth: false, skipAuthRefresh: true },
    )
    return persistAuth(data)
  },

  async registerPatient(payload: PatientRegisterPayload): Promise<RegisterResult> {
    const data = await api.post<
      AuthResponse | { needs_email_verification?: boolean; email?: string; detail?: string }
    >('/auth/register/patient/', payload, {
      auth: false,
      skipAuthRefresh: true,
    })
    if (data && 'needs_email_verification' in data && data.needs_email_verification) {
      return {
        kind: 'needs_email_verification',
        email: typeof data.email === 'string' ? data.email : '',
        detail: typeof data.detail === 'string' ? data.detail : 'Sprawdź e-mail i wpisz kod.',
      }
    }
    if (data && 'user' in data && data.user) {
      const user = await persistAuth(data as AuthResponse)
      return { kind: 'authenticated', user }
    }
    throw new Error('Nieoczekiwana odpowiedź rejestracji.')
  },

  async verifyEmail(email: string, code: string) {
    const data = await api.post<AuthResponse>(
      '/auth/email/verify/',
      { email, code },
      { auth: false, skipAuthRefresh: true },
    )
    return persistAuth(data)
  },

  resendEmailCode(email: string) {
    return api.post<{ detail: string }>(
      '/auth/email/resend/',
      { email },
      { auth: false, skipAuthRefresh: true },
    )
  },

  requestPasswordReset(email: string) {
    return api.post<{ detail: string }>(
      '/auth/password-reset/request/',
      { email, client: 'mobile' },
      { auth: false, skipAuthRefresh: true },
    )
  },

  verifyPasswordResetCode(email: string, code: string) {
    return api.post<{ detail: string; reset_token: string }>(
      '/auth/password-reset/verify/',
      { email, code },
      { auth: false, skipAuthRefresh: true },
    )
  },

  confirmPasswordReset(payload: PasswordResetConfirmPayload) {
    return api.post<{ detail: string }>('/auth/password-reset/confirm/', payload, {
      auth: false,
      skipAuthRefresh: true,
    })
  },

  async logout() {
    try {
      const refresh = await tokenStorage.getRefresh()
      await api.post<{ detail: string }>('/auth/logout/', refresh ? { refresh } : {}, {
        skipAuthRefresh: true,
      })
    } finally {
      await tokenStorage.clear()
    }
  },

  changePassword(current_password: string, new_password: string) {
    return api.post<{ detail: string }>('/auth/password-change/', {
      current_password,
      new_password,
    })
  },
}
