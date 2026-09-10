export type UserRole = 'PATIENT' | 'THERAPIST'

export type VisitStatus = 'PENDING_APPROVAL' | 'SCHEDULED' | 'COMPLETED' | 'CANCELLED' | 'NO_SHOW'

export type MediaType = 'VIDEO' | 'PDF'

export type CategoryKind = 'TYPE' | 'REGION' | 'MUSCLE' | 'INJURY'

export interface ExerciseCategory {
  id: string
  name: string
  kind: CategoryKind
  slug: string
}

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
  patient_avatar_url: string
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
  patient_summary: string
  patient_note: string
  cancel_reason: string
  created_at: string
}

export interface TherapyType {
  id: string
  name: string
  color_hex: string
  duration_min: number
  created_at: string
}

export interface VisitRequestPayload {
  therapy_type_id: string
  start_at: string
  end_at: string
  patient_note?: string
}

export interface TodayExercise {
  id: string
  exercise: string
  exercise_title: string
  exercise_instruction: string
  exercise_file_url: string
  exercise_media_type: MediaType
  categories?: ExerciseCategory[]
  patient: string
  episode: string | null
  dosage: string
  start_date: string
  end_date: string
  assigned_at: string
  completed_today: boolean
}

export interface ExercisePlanItem extends TodayExercise {
  completions: ExerciseCompletion[]
  is_active: boolean
}

export type EpisodeStatus = 'IN_PROGRESS' | 'COMPLETED_SUCCESS' | 'REFERRED' | 'INTERRUPTED'

export interface TreatmentEpisode {
  id: string
  icd10_code: string
  functional_diagnosis: string
  status: EpisodeStatus
  status_label: string
  summary_note: string
  started_at: string
  ended_at: string | null
  created_at: string
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

export type ClinicalDocumentKind =
  | 'recommendation'
  | 'device_order'
  | 'refusal'
  | 'recepta_na_ruch'
  | 'pdf'

export interface ClinicalDocumentItem {
  id: string
  kind: ClinicalDocumentKind
  kind_label: string
  title: string
  summary: string
  created_at: string
  therapist_name: string
  episode_id: string | null
  status: string | null
  file_url: string | null
  details: Record<string, unknown>
}

export interface CompetenceCapability {
  code: string
  allowed: boolean
  label: string
  detail: string
}

export interface CompetenceSnapshot {
  qualification_level: string
  qualification_label: string
  experience_years: number
  is_magister_or_above: boolean
  is_fizjo_spec: boolean
  can_plan_therapy: boolean
  can_supervise: boolean
  device_groups: string[]
  capabilities: CompetenceCapability[]
}

export interface TherapistPublic {
  id: string
  first_name: string
  last_name: string
  bio: string
  courses: string[]
  avatar_url: string
  phone: string
  location_address: string
  qualification_level?: string
  qualification_label?: string
  experience_years?: number
  competences?: CompetenceSnapshot
}

export type NotificationPrefKey =
  'visit_reminder' | 'visit_change' | 'waitlist' | 'exercise_reminder' | 'new_document'

export interface NotificationPreference {
  pref_key: NotificationPrefKey | string
  enabled: boolean
}

export interface DeviceToken {
  id: string
  expo_push_token: string
  platform: 'ios' | 'android' | 'unknown'
  is_active: boolean
  updated_at: string
}
