/**
 * @file types.ts
 * @description Główny plik definicji typów TypeScript dla warstwy komunikacji API systemu PhysioCare (DTO, modele danych, interfejsy).
 */

export type UserRole = 'PATIENT' | 'THERAPIST' | 'ADMIN'

export type VisitStatus = 'PENDING_APPROVAL' | 'SCHEDULED' | 'COMPLETED' | 'CANCELLED' | 'NO_SHOW'

export interface User {
  id: string
  email: string
  role: UserRole
  first_name: string
  last_name: string
  avatar_url?: string | null
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

export type QualificationLevel = 'TECHNIK' | 'LICENCJAT' | 'MAGISTER' | 'FIZJO_SPEC'

export interface CompetenceCapability {
  code: string
  allowed: boolean
  label: string
  detail: string
}

export interface CompetenceSnapshot {
  qualification_level: QualificationLevel
  qualification_label: string
  experience_years: number
  is_magister_or_above: boolean
  is_fizjo_spec: boolean
  can_plan_therapy: boolean
  can_supervise: boolean
  device_groups: string[]
  capabilities: CompetenceCapability[]
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
  qualification_level: QualificationLevel
  experience_years: number
  competences?: CompetenceSnapshot
  created_at: string
}

export type RecommendationType =
  'SPECIALIST_CONSULTATION' | 'IMAGING_MRI' | 'IMAGING_CT' | 'IMAGING_RTG' | 'IMAGING_USG' | 'OTHER'

export type FundingHint = 'NFZ_VIA_DOCTOR' | 'PRIVATE' | 'NOT_APPLICABLE'

export type DeviceOrderStatus = 'DRAFT' | 'ISSUED' | 'CANCELLED'

export type BodySide = 'LEFT' | 'RIGHT' | 'BOTH' | 'NA'

export interface DiagnosticRecommendation {
  id: string
  episode: string
  therapist: string
  therapist_name?: string
  is_read_only?: boolean
  recommendation_type: RecommendationType
  target_specialty: string
  body_area: string
  justification: string
  red_flags_noted: boolean
  funding_hint: FundingHint
  created_at: string
}

export interface MedicalDeviceOrder {
  id: string
  episode: string
  patient: string
  therapist: string
  therapist_name?: string
  is_read_only?: boolean
  device_code: string
  device_group: string
  device_name: string
  side: BodySide
  quantity: number
  icd10_code: string
  access_code: string
  status: DeviceOrderStatus
  notes: string
  created_at: string
}

export interface PhysicianOrderRefusal {
  id: string
  episode: string
  therapist: string
  therapist_name?: string
  is_read_only?: boolean
  physician_order_description: string
  refusal_reason: string
  physician_notified: boolean
  created_at: string
}

export interface ReceptaNaRuchReferral {
  id: string
  patient: string
  therapist: string
  therapist_name?: string
  is_read_only?: boolean
  episode: string | null
  readiness_confirmed: boolean
  activity_notes: string
  status: DeviceOrderStatus
  created_at: string
}

export interface MedicalDeviceCatalogItem {
  code: string
  group: string
  name: string
  min_qualification: QualificationLevel
  usage_hint: string
  allowed_for_therapist: boolean
}

export interface MedicalDeviceCatalog {
  groups: {
    magister_groups: string[]
    fizjo_spec_extra_groups: string[]
  }
  items: MedicalDeviceCatalogItem[]
  competences: CompetenceSnapshot
  disclaimer: string
}

export interface DashboardStats {
  visits_today: number
  patients_total: number
  assignments_active?: number
  rating_avg?: number | string
  rating_count?: number
}

/** Opinia pacjenta o fizjoterapeucie */
export interface ReviewItem {
  id: string
  rating: number
  comment: string
  author_name: string
  author_avatar_url?: string | null
  is_anonymous: boolean
  is_verified: boolean
  is_own?: boolean
  created_at: string
  therapist_reply: string
  therapist_replied_at: string | null
}

/** Podsumowanie ocen fizjoterapeuty */
export interface RatingSummary {
  average_rating: string | number
  total_reviews: number
  rating_breakdown: Record<string, number>
}

export interface PatientSummary {
  id: string
  email: string
  first_name: string
  last_name: string
  phone: string | null
  avatar_url: string | null
}

export interface AvailabilitySlot {
  id: string
  therapist: string
  start_at: string | null
  end_at: string | null
  day_of_week: number | null
  start_time: string | null
  end_time: string | null
  is_recurring: boolean
  is_active: boolean
  created_at: string
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
  patient_avatar_url: string | null
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

export interface VisitCreatePayload {
  patient_id: string
  therapy_type_id: string
  episode_id?: string | null
  start_at: string
  end_at: string
  prep_instructions?: string
}

export interface VisitUpdatePayload {
  therapy_type_id?: string
  start_at?: string
  end_at?: string
  prep_instructions?: string
  patient_summary?: string
  location_address?: string
  status?: VisitStatus
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
  therapist?: string | null
  therapist_name?: string
  is_read_only?: boolean
  icd10_code: string
  functional_diagnosis: string
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
  therapist?: string | null
  therapist_name?: string
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

export interface Holiday {
  date: string
  name: string
}

export interface AvailableSlotsResponse {
  results: AvailabilitySlot[]
  is_holiday?: boolean
  holiday_name?: string | null
}

/** Zbiorcze metryki i analityka KPI dla pulpitu administratora. */
export interface AdminDashboardStats {
  users: {
    total: number
    patients_count: number
    therapists_count: number
    admins_count: number
    active_count: number
    inactive_count: number
    new_last_30_days: number
  }
  visits: {
    total: number
    scheduled: number
    completed: number
    cancelled: number
    no_show: number
    pending_approval: number
    show_up_rate_percent: number
  }
  quality: {
    rating_avg: number
    rating_count: number
  }
  exercises: {
    total_exercises: number
    total_assignments: number
  }
}

/** Element listy użytkowników w widoku zarządzania kontami w panelu admina. */
export interface AdminUserListItem {
  id: string
  email: string
  first_name: string
  last_name: string
  role: UserRole
  is_active: boolean
  is_staff: boolean
  email_verified: boolean
  created_at: string
  last_login?: string | null
}

/** Pełne szczegóły profilu użytkownika dla administratora. */
export interface AdminUserDetail extends AdminUserListItem {
  is_superuser: boolean
  updated_at: string
  google_linked: boolean
  has_mfa: boolean
  visits_count: number
  profile_info?: {
    pwzf_number?: string
    phone?: string
    qualification_level?: string
    experience_years?: number
    rating_avg?: number
    rating_count?: number
    avatar_url?: string
  } | null
}

/** Zestawienie statystyk pracy i efektywności pojedynczego fizjoterapeuty. */
export interface AdminTherapistStats {
  therapist_id: string
  user_id: string
  first_name: string
  last_name: string
  email: string
  pwzf_number: string
  qualification_level: string
  experience_years: number
  rating_avg: number
  rating_count: number
  total_visits: number
  completed_visits: number
  cancelled_visits: number
  no_show_visits: number
  pending_visits: number
}

/** Podsumowanie wizyty w zbiorczym widoku harmonogramu administratora. */
export interface AdminVisitSummary {
  id: string
  start_at: string
  end_at: string
  status: VisitStatus
  location_address: string
  patient_name: string
  therapist_name: string
  therapist_id: string
  therapy_type_name: string
  therapy_type_color: string
}

/** Slot dostępności fizjoterapeuty w zbiorczym harmonogramie. */
export interface AdminAvailabilitySlot {
  id: string
  therapist_id: string
  start_at: string | null
  end_at: string | null
  day_of_week: number | null
  start_time: string | null
  end_time: string | null
  is_recurring: boolean
  is_active: boolean
}

/** Zbiorczy przegląd grafiku wizyt i dostępności personelu w zadanym oknie czasu. */
export interface AdminSchedulingOverview {
  range: {
    start_at: string
    end_at: string
  }
  therapists: Array<{
    id: string
    user_id: string
    name: string
    email: string
    qualification_level: string
    rating_avg: number
    rating_count: number
  }>
  visits: AdminVisitSummary[]
  availability_slots: AdminAvailabilitySlot[]
}

/** Recenzja pacjenta w widoku moderacji opinii panelu administratora. */
export interface AdminReview {
  id: string
  patient_id: string
  patient_name: string
  therapist_id: string
  therapist_name: string
  visit_id: string | null
  rating: number
  comment: string
  is_anonymous: boolean
  is_visible: boolean
  therapist_reply: string
  therapist_replied_at: string | null
  created_at: string
}

