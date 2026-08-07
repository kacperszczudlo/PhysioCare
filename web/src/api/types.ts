export type UserRole = 'PATIENT' | 'THERAPIST'

export type VisitStatus = 'SCHEDULED' | 'COMPLETED' | 'CANCELLED' | 'NO_SHOW'

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

export interface TherapistProfile {
  id: string
  email: string
  first_name: string
  last_name: string
  pwzf_number: string
  phone: string | null
  location_address: string | null
  bio: string | null
  courses: string[]
  avatar_url: string | null
  created_at: string
}

export interface DashboardStats {
  visits_today: number
  patients_total: number
  assignments_active?: number
}

export interface PatientSummary {
  id: string
  email: string
  first_name: string
  last_name: string
  phone: string | null
  avatar_url: string | null
}

export interface TherapyType {
  id: string
  name: string
  color_hex: string
  duration_min: number
  created_at: string
}

export type TherapyTypePresetGroup = 'kind' | 'profile'

export interface TherapyTypePreset {
  group: TherapyTypePresetGroup
  name: string
  color_hex: string
  duration_min: number
  description: string
  already_added: boolean
}

export interface Visit {
  id: string
  patient: string
  therapist: string
  episode: string | null
  therapy_type: string
  patient_first_name: string
  patient_last_name: string
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

export interface VisitCreatePayload {
  patient_id: string
  therapy_type_id: string
  episode_id?: string | null
  start_at: string
  end_at: string
  prep_instructions?: string
}

export type EpisodeStatus = 'IN_PROGRESS' | 'COMPLETED_SUCCESS' | 'REFERRED' | 'INTERRUPTED'

export type BodyViewSide = 'FRONT' | 'BACK'

export interface PatientDetail extends PatientSummary {
  pesel: string | null
  therapist: string
  created_at: string
}

export interface TreatmentEpisode {
  id: string
  patient: string
  icd10_code: string
  status: EpisodeStatus
  summary_note: string
  started_at: string
  ended_at: string | null
  created_at: string
}

export interface BodyAreaPain {
  id: string
  episode: string
  body_region: string
  view_side: BodyViewSide
  vas_score: number
  pain_character: string[]
  treatment_targets: string[]
  recorded_at: string
}

export interface VisitNote {
  id: string
  episode: string
  visit: string | null
  content: string
  created_at: string
}

export type MediaType = 'VIDEO' | 'PDF'

export type CategoryKind = 'TYPE' | 'REGION' | 'MUSCLE' | 'INJURY'

export interface ExerciseCategory {
  id: string
  name: string
  kind: CategoryKind
  slug: string
}

export interface Exercise {
  id: string
  title: string
  media_type: MediaType
  file_url: string
  instruction: string
  created_at: string
  categories: ExerciseCategory[]
}

export interface ExerciseAssignment {
  id: string
  exercise: string
  exercise_title: string
  exercise_instruction?: string
  exercise_file_url?: string
  exercise_media_type?: MediaType
  patient: string
  episode: string | null
  dosage: string
  start_date: string
  end_date: string
  assigned_at: string
}

export interface ExerciseAssignmentPayload {
  exercise_id: string
  patient_id: string
  episode_id?: string | null
  dosage: string
  start_date: string
  end_date: string
}

export interface ExerciseAssignmentUpdatePayload {
  dosage?: string
  start_date?: string
  end_date?: string
  episode_id?: string | null
}
