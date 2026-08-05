import { api } from './client'
import type {
  Consent,
  ExerciseCompletion,
  MedicalDocument,
  NotificationPreference,
  Paginated,
  PatientProfile,
  TherapistPublic,
  TodayExercise,
  Visit,
} from './types'

function unwrapList<T>(data: T[] | Paginated<T>): T[] {
  return Array.isArray(data) ? data : data.results
}

export const patientApi = {
  getProfile() {
    return api.get<PatientProfile>('/me/profile/')
  },

  updateProfile(payload: Partial<Pick<PatientProfile, 'pesel' | 'phone' | 'avatar_url'>>) {
    return api.patch<PatientProfile>('/me/profile/', payload)
  },

  async getConsents() {
    const data = await api.get<Consent[] | Paginated<Consent>>('/me/consents/')
    return unwrapList(data)
  },

  updateOptionalConsents(payload: { marketing?: boolean; research?: boolean }) {
    return api.patch<Consent[]>('/me/consents/optional/', payload)
  },

  requestDataExport() {
    return api.post<{ profile: PatientProfile; consents: Consent[] }>('/me/data-export/')
  },

  requestAccountDeletion() {
    return api.post<{ detail: string }>('/me/account-deletion-request/')
  },

  async getVisits(status: 'upcoming' | 'past') {
    const data = await api.get<Visit[] | Paginated<Visit>>(`/me/visits/?status=${status}`)
    return unwrapList(data)
  },

  getVisit(id: string) {
    return api.get<Visit>(`/visits/${id}/`)
  },

  rescheduleVisit(id: string, payload: { start_at: string; end_at: string }) {
    return api.patch<Visit>(`/visits/${id}/reschedule/`, payload)
  },

  cancelVisit(id: string, cancel_reason = '') {
    return api.post<Visit>(`/visits/${id}/cancel/`, { cancel_reason })
  },

  async getExercisesToday() {
    const data = await api.get<TodayExercise[] | Paginated<TodayExercise>>(
      '/me/exercises/today/',
    )
    return unwrapList(data)
  },

  completeExercise(assignment_id: string, completed_on?: string) {
    return api.post<ExerciseCompletion>('/me/exercise-completions/', {
      assignment_id,
      completed_on,
      done: true,
    })
  },

  async getDocuments() {
    const data = await api.get<MedicalDocument[] | Paginated<MedicalDocument>>(
      '/me/documents/',
    )
    return unwrapList(data)
  },

  getTherapistPublic(id: string) {
    return api.get<TherapistPublic>(`/therapists/${id}/public/`)
  },

  async getNotificationPreferences() {
    const data = await api.get<
      NotificationPreference[] | Paginated<NotificationPreference>
    >('/me/notification-preferences/')
    return unwrapList(data)
  },

  updateNotificationPreferences(preferences: Record<string, boolean>) {
    return api.patch<NotificationPreference[]>('/me/notification-preferences/', {
      preferences,
    })
  },
}
