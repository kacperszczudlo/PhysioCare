/**
 * @file types.ts
 * @description Definicje typów, interfejsów DTO oraz struktur danych wymienianych między aplikacją mobilną a backendem API PhysioCare.
 */

/** Rola użytkownika w systemie */
export type UserRole = 'PATIENT' | 'THERAPIST'

/** Status wizyty fizjoterapeutycznej */
export type VisitStatus = 'PENDING_APPROVAL' | 'SCHEDULED' | 'COMPLETED' | 'CANCELLED' | 'NO_SHOW'

/** Typ załączonego pliku multimedialnego ćwiczenia */
export type MediaType = 'VIDEO' | 'PDF'

/** Kategoria lub klasyfikacja ćwiczenia fizjoterapeutycznego */
export type CategoryKind = 'TYPE' | 'REGION' | 'MUSCLE' | 'INJURY'

/** Interfejs reprezentujący kategorię ćwiczenia */
export interface ExerciseCategory {
  /** Identyfikator kategorii */
  id: string
  /** Nazwa kategorii */
  name: string
  /** Rodzaj kategorii */
  kind: CategoryKind
  /** Przejrzysty identyfikator słowny (slug) */
  slug: string
}

/** Podstawowy obiekt zalogowanego użytkownika */
export interface User {
  /** Unikalny identyfikator (UUID) */
  id: string
  /** Adres e-mail */
  email: string
  /** Rola w systemie */
  role: UserRole
  /** Imię */
  first_name: string
  /** Nazwisko */
  last_name: string
}

/** Struktura ciała błędu zwracanego przez backend API */
export interface ApiErrorBody {
  error?: {
    code?: string
    message?: string
    details?: Record<string, unknown>
  }
  detail?: string
  [key: string]: unknown
}

/** Uniwersalna struktura dla stronnicowanych odpowiedzi API */
export interface Paginated<T> {
  /** Łączna liczba wszystkich elementów w bazie */
  count: number
  /** Link do następnej strony (jeśli istnieje) */
  next: string | null
  /** Link do poprzedniej strony (jeśli istnieje) */
  previous: string | null
  /** Tablica wyników dla bieżącej strony */
  results: T[]
}

/** Para tokenów autoryzacyjnych JWT */
export interface AuthTokens {
  /** Token dostępowy o krótkim czasie ważności */
  access: string
  /** Token odświeżający o dłuższym czasie ważności */
  refresh: string
}

/** Odpowiedź z serwera po pomyślnym zalogowaniu */
export interface AuthResponse {
  /** Dane zalogowanego użytkownika */
  user: User
  /** Access token JWT */
  access: string
  /** Refresh token JWT */
  refresh: string
}

/** Pełny profil pacjenta w systemie */
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

/** Udzielona zgoda prawna lub marketingowa */
export interface Consent {
  consent_type: string
  granted: boolean
  granted_at: string
}

/** Obiekt pojedynczej wizyty pacjenta */
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

/** Usługa lub rodzaj zabiegu fizjoterapeutycznego */
export interface TherapyType {
  id: string
  name: string
  color_hex: string
  duration_min: number
  created_at: string
}

/** Ładunek zgłoszenia nowej rezerwacji wizyty */
export interface VisitRequestPayload {
  therapist_id?: string
  therapy_type_id: string
  start_at: string
  end_at: string
  patient_note?: string
}

/** Ćwiczenie zaplanowane do wykonania na dzisiejszy dzień */
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

/** Pozycja z pełnego planu ćwiczeń wraz z historią zaliczeń */
export interface ExercisePlanItem extends TodayExercise {
  completions: ExerciseCompletion[]
  is_active: boolean
}

/** Status trwania epizodu leczenia fizjoterapeutycznego */
export type EpisodeStatus = 'IN_PROGRESS' | 'COMPLETED_SUCCESS' | 'REFERRED' | 'INTERRUPTED'

/** Epizod leczenia (cykl terapeutyczny) pacjenta */
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

/** Rekord zaliczenia wykonania ćwiczenia domowego */
export interface ExerciseCompletion {
  id: string
  assignment: string
  completed_on: string
  done: boolean
  completed_at: string
}

/** Dokument medyczny przesłany lub powiązany z pacjentem */
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

/** Kategoria generowanego pliku lub dokumentu klinicznego */
export type ClinicalDocumentKind =
  'recommendation' | 'device_order' | 'refusal' | 'recepta_na_ruch' | 'pdf'

/** Pozycja dokumentu klinicznego wystawionego przez fizjoterapeutę */
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

/** Uprawnienie zawodowe lub kompetencyjne fizjoterapeuty */
export interface CompetenceCapability {
  code: string
  allowed: boolean
  label: string
  detail: string
}

/** Migawka kwalifikacji i kompetencji zawodowych fizjoterapeuty */
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

/** Publiczne dane wizytówkowe fizjoterapeuty */
export interface TherapistPublic {
  id: string
  first_name: string
  last_name: string
  bio: string
  courses: string[]
  avatar_url: string
  phone: string
  location_address: string
  pwzf_number?: string
  qualification_level?: string
  qualification_label?: string
  experience_years?: number
  competences?: CompetenceSnapshot
}

/** Klucz preferencji powiadomień Push */
export type NotificationPrefKey =
  'visit_reminder' | 'visit_change' | 'waitlist' | 'exercise_reminder' | 'new_document'

/** Wpis pojedynczej preferencji powiadomień */
export interface NotificationPreference {
  pref_key: NotificationPrefKey | string
  enabled: boolean
}

/** Token powiadomień urządzenia mobilnego */
export interface DeviceToken {
  id: string
  expo_push_token: string
  platform: 'ios' | 'android' | 'unknown'
  is_active: boolean
  updated_at: string
}

/** Ładunek zrzutu eksportu danych osobowych pacjenta w ramach RODO (Art. 15) */
export interface PatientDataExport {
  exported_at: string
  profile: PatientProfile
  consents: Consent[]
  visits: {
    id: string
    start_at: string
    end_at: string
    status: string
    therapy_type: string | null
    location_address: string
    prep_instructions: string
    patient_summary: string
    patient_note: string
    cancel_reason: string
  }[]
  episodes: {
    id: string
    icd10_code: string
    functional_diagnosis: string
    status: string
    summary_note: string
    started_at: string | null
    ended_at: string | null
    body_pain: {
      body_region: string
      view_side: string
      vas_score: number
      pain_character: string
      treatment_targets: string
    }[]
  }[]
  documents: {
    id: string
    title: string
    mime_type: string
    created_at: string
    file_url: string
  }[]
  exercise_assignments: {
    id: string
    exercise_title: string
    dosage: string
    start_date: string
    end_date: string
    completions: {
      completed_on: string
      done: boolean
    }[]
  }[]
  device_orders: {
    id: string
    device_code: string
    device_name: string
    access_code: string
    status: string
  }[]
  diagnostic_recommendations: {
    id: string
    recommendation_type: string
    justification: string
  }[]
  physician_order_refusals: {
    id: string
    refusal_reason: string
  }[]
  recepta_na_ruch: {
    id: string
    status: string
    activity_notes: string
  }[]
  notification_preferences: NotificationPreference[]
  device_tokens: {
    id: string
    platform: string
    is_active: boolean
    updated_at: string
    token_fingerprint: string
  }[]
  notification_deliveries: {
    pref_key: string
    channel: string
    status: string
    title: string
    body: string
    data: Record<string, unknown>
    created_at: string
  }[]
}
