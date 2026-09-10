import { api } from './client'
import type {
  ClinicalDocumentItem,
  ClinicalDocumentKind,
  Consent,
  DeviceToken,
  ExerciseCompletion,
  MedicalDocument,
  NotificationPreference,
  Paginated,
  PatientProfile,
  TherapistPublic,
  TherapyType,
  TodayExercise,
  Visit,
  VisitRequestPayload,
} from './types'

function unwrapList<T>(data: T[] | Paginated<T>): T[] {
  return Array.isArray(data) ? data : data.results
}

export const patientApi = {
  getProfile() {
    return api.get<PatientProfile>('/me/profile/')
  },

  updateProfile(payload: Partial<Pick<PatientProfile, 'pesel' | 'phone'>>) {
    return api.patch<PatientProfile>('/me/profile/', payload)
  },

  uploadAvatar(uri: string, mimeType = 'image/jpeg', fileName = 'avatar.jpg') {
    const body = new FormData()
    body.append('file', {
      uri,
      type: mimeType,
      name: fileName,
    } as unknown as Blob)
    return api.post<PatientProfile>('/me/profile/avatar/', body)
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

  requestAccountDeletion(reason?: string) {
    return api.post<{ detail: string }>('/me/account-deletion-request/', {
      reason: reason ?? '',
    })
  },

  async getVisits(status: 'upcoming' | 'past') {
    const data = await api.get<Visit[] | Paginated<Visit>>(`/me/visits/?status=${status}`)
    return unwrapList(data)
  },

  getVisit(id: string) {
    return api.get<Visit>(`/visits/${id}/`)
  },

  requestVisit(payload: VisitRequestPayload) {
    return api.post<Visit>('/me/visits/', payload)
  },

  async getTherapyTypes() {
    const data = await api.get<TherapyType[] | Paginated<TherapyType>>('/me/therapy-types/')
    return unwrapList(data)
  },

  rescheduleVisit(id: string, payload: { start_at: string; end_at: string }) {
    return api.patch<Visit>(`/visits/${id}/reschedule/`, payload)
  },

  cancelVisit(id: string, cancel_reason = '') {
    return api.post<Visit>(`/visits/${id}/cancel/`, { cancel_reason })
  },

  async getExercisesToday() {
    const data = await api.get<TodayExercise[] | Paginated<TodayExercise>>('/me/exercises/today/')
    return unwrapList(data)
  },

  completeExercise(assignment_id: string, completed_on?: string, done = true) {
    return api.post<ExerciseCompletion>('/me/exercise-completions/', {
      assignment_id,
      done,
      ...(completed_on ? { completed_on } : {}),
    })
  },

  async getDocuments() {
    const data = await api.get<MedicalDocument[] | Paginated<MedicalDocument>>('/me/documents/')
    return unwrapList(data)
  },

  async getClinicalDocuments(kind?: ClinicalDocumentKind) {
    const query = kind ? `?kind=${kind}` : ''
    const data = await api.get<{ count: number; results: ClinicalDocumentItem[] }>(
      `/me/clinical-documents/${query}`,
    )
    return data.results
  },

  getTherapistPublic(id: string) {
    return api.get<TherapistPublic>(`/therapists/${id}/public/`)
  },

  async getNotificationPreferences() {
    const data = await api.get<NotificationPreference[] | Paginated<NotificationPreference>>(
      '/me/notification-preferences/',
    )
    return unwrapList(data)
  },

  updateNotificationPreferences(preferences: Record<string, boolean>) {
    return api.patch<NotificationPreference[]>('/me/notification-preferences/', {
      preferences,
    })
  },

  registerDeviceToken(expoPushToken: string, platform: DeviceToken['platform'] = 'unknown') {
    return api.post<DeviceToken>('/me/device-tokens/', {
      expo_push_token: expoPushToken,
      platform,
    })
  },

  unregisterDeviceToken(expoPushToken: string) {
    return api.delete<void>('/me/device-tokens/', {
      body: { expo_push_token: expoPushToken },
    })
  },
}
