export type UserRole = 'PATIENT' | 'THERAPIST'

export interface User {
  id: string
  email: string
  role: UserRole
  first_name: string
  last_name: string
}

export interface ApiErrorBody {
  error?: {
    code?: string
    message?: string
    details?: Record<string, unknown>
  }
  detail?: string
  [key: string]: unknown
}

export interface TherapistProfile {
  id: string
  email: string
  first_name: string
  last_name: string
  pwzf_number: string
  phone: string | null
  bio: string | null
  courses: string[]
  avatar_url: string | null
  created_at: string
}

export interface DashboardStats {
  visits_today: number
  patients_total: number
}
