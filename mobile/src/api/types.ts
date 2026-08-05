export type UserRole = 'PATIENT' | 'THERAPIST'

export type VisitStatus = 'SCHEDULED' | 'COMPLETED' | 'CANCELLED' | 'NO_SHOW'

export type MediaType = 'VIDEO' | 'PDF'

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

export interface Paginated<T> {
  count: number
  next: string | null
  previous: string | null
  results: T[]
}

export interface AuthTokens {
  access: string
  refresh: string
}

export interface AuthResponse {
  user: User
  access: string
  refresh: string
}

export interface PatientProfile {
  id: string
  email: string
  first_name: string
  last_name: string
  pesel: string | null
  phone: string
  avatar_url: string
  therapist: string
}

export interface Consent {
  consent_type: string
  granted: boolean
  granted_at: string
}

export interface Visit {
  id: string
  patient: string
  therapist: string
  episode: string | null
  therapy_type: string
  patient_first_name: string
  patient_last_name: string
  therapist_first_name: string
  therapist_last_name: string
  therapy_type_name: string
  therapy_type_color: string
  therapy_type_duration_min: number
  start_at: string
  end_at: string
  status: VisitStatus
  location_address: string
  prep_instructions: string
  cancel_reason: string
  created_at: string
}

export interface TodayExercise {
  id: string
  exercise: string
  exercise_title: string
  exercise_instruction: string
  exercise_file_url: string
  exercise_media_type: MediaType
  patient: string
  episode: string | null
  dosage: string
  start_date: string
  end_date: string
  assigned_at: string
  completed_today: boolean
}

export interface ExerciseCompletion {
  id: string
  assignment: string
  completed_on: string
  done: boolean
  completed_at: string
}

export interface MedicalDocument {
  id: string
  title: string
  file_url: string
  mime_type: string
  visit: string | null
  episode: string | null
  uploaded_by: string
  created_at: string
}

export interface TherapistPublic {
  id: string
  first_name: string
  last_name: string
  bio: string
  courses: string[]
  avatar_url: string
  phone: string
}

export interface NotificationPreference {
  pref_key: string
  enabled: boolean
}
