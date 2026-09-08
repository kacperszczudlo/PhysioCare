import { api } from './client'
import { tokenStorage } from './tokenStorage'
import type { AuthResponse, User } from './types'

export interface PatientRegisterPayload {
  email: string
  password: string
  first_name: string
  last_name: string
  therapist_id: string
  phone?: string
  consents: {
    terms: boolean
    medical_data: boolean
  }
}

export interface PasswordResetConfirmPayload {
  token: string
  new_password: string
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

  async registerPatient(payload: PatientRegisterPayload) {
    const data = await api.post<AuthResponse>('/auth/register/patient/', payload, {
      auth: false,
      skipAuthRefresh: true,
    })
    return persistAuth(data)
  },

  requestPasswordReset(email: string) {
    return api.post<{ detail: string }>(
      '/auth/password-reset/request/',
      { email, client: 'mobile' },
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
