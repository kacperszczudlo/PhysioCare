import { api } from './client'
import type { Paginated, TherapyType, Visit, VisitCreatePayload } from './types'

async function listResults<T>(path: string): Promise<T[]> {
  const page = await api.get<Paginated<T> | T[]>(path)
  return Array.isArray(page) ? page : page.results
}

export const schedulingApi = {
  listVisitsForDate(dateIso: string) {
    return listResults<Visit>(`/therapist/visits/?date=${encodeURIComponent(dateIso)}`)
  },

  /** Scheduled visits that are still ongoing or start in the future (any day). */
  listUpcomingVisits() {
    return listResults<Visit>('/therapist/visits/?upcoming=1')
  },

  createVisit(payload: VisitCreatePayload) {
    return api.post<Visit>('/therapist/visits/', payload)
  },

  updateVisitTimes(id: string, start_at: string, end_at: string) {
    return api.patch<Visit>(`/therapist/visits/${id}/`, { start_at, end_at })
  },

  cancelVisit(id: string, cancel_reason = '') {
    return api.post<Visit>(`/visits/${id}/cancel/`, { cancel_reason })
  },

  listTherapyTypes() {
    return listResults<TherapyType>('/therapist/therapy-types/')
  },

  createTherapyType(payload: { name: string; color_hex?: string; duration_min?: number }) {
    return api.post<TherapyType>('/therapist/therapy-types/', payload)
  },
}
