import { api } from './client'
import type { DashboardStats, TherapistProfile, User } from './types'

interface AuthResponse {
  user: User
}

export interface TherapistRegisterPayload {
  email: string
  password: string
  first_name: string
  last_name: string
  pwzf_number: string
  pwzf_declaration: boolean
}

export interface PasswordResetConfirmPayload {
  token: string
  new_password: string
}

export const authApi = {
  login(email: string, password: string) {
    return api.post<AuthResponse>('/auth/login/', { email, password }, { skipAuthRefresh: true })
  },

  registerTherapist(payload: TherapistRegisterPayload) {
    return api.post<AuthResponse>('/auth/register/therapist/', payload, {
      skipAuthRefresh: true,
    })
  },

  requestPasswordReset(email: string) {
    return api.post<{ detail: string }>(
      '/auth/password-reset/request/',
      { email },
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
  bio?: string
  courses?: string[]
}

export const therapistApi = {
  getProfile() {
    return api.get<TherapistProfile>('/therapist/profile/')
  },

  updateProfile(payload: TherapistProfileUpdatePayload) {
    return api.patch<TherapistProfile>('/therapist/profile/', payload)
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
