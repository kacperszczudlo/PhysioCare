import { api } from './client'
import type {
  AvailabilitySlot,
  AvailableSlotsResponse,
  Holiday,
  Paginated,
  TherapyType,
  TherapyTypePreset,
  Visit,
  VisitCreatePayload,
  VisitUpdatePayload,
} from './types'

async function listResults<T>(path: string): Promise<T[]> {
  const page = await api.get<Paginated<T> | T[]>(path)
  return Array.isArray(page) ? page : page.results
}

/** Usługi API do zarządzania wizytami, harmonogramem pracy fizjoterapeuty i dniami wolnymi. */
export const schedulingApi = {
  /** Pobiera listę wizyt zaplanowanych na konkretny dzień (ISO Date). */
  listVisitsForDate(dateIso: string) {
    return listResults<Visit>(`/therapist/visits/?date=${encodeURIComponent(dateIso)}`)
  },

  /** Pobiera listę najbliższych nadchodzących wizyt z opcjonalnym limitem. */
  listUpcomingVisits(limit?: number) {
    const params = new URLSearchParams({ upcoming: '1' })
    if (limit != null && limit > 0) {
      params.set('limit', String(limit))
    }
    return listResults<Visit>(`/therapist/visits/?${params}`)
  },

  /** Tworzy nową wizytę w kalendarzu. */
  createVisit(payload: VisitCreatePayload) {
    return api.post<Visit>('/therapist/visits/', payload)
  },

  /** Aktualizuje dane istniejącej wizyty. */
  updateVisit(id: string, payload: VisitUpdatePayload) {
    return api.patch<Visit>(`/therapist/visits/${id}/`, payload)
  },

  /** Zmienia godziny rozpoczęcia i zakończenia wizyty (np. drag & drop w kalendarzu). */
  updateVisitTimes(id: string, start_at: string, end_at: string) {
    return api.patch<Visit>(`/therapist/visits/${id}/`, { start_at, end_at })
  },

  /** Zmienia rodzaj terapii przypisany do wizyty. */
  updateVisitType(id: string, therapy_type_id: string) {
    return api.patch<Visit>(`/therapist/visits/${id}/`, { therapy_type_id })
  },

  /** Anuluje wizytę z podaniem przyczyny. */
  cancelVisit(id: string, cancel_reason = '') {
    return api.post<Visit>(`/visits/${id}/cancel/`, { cancel_reason })
  },

  /** Pobiera listę wizyt oczekujących na zatwierdzenie. */
  listPendingVisits() {
    return listResults<Visit>('/therapist/visits/?pending=1')
  },

  /** Zatwierdza wizytę ze stanu oczekującego. */
  approveVisit(id: string, payload: VisitUpdatePayload = {}) {
    return api.post<Visit>(`/therapist/visits/${id}/approve/`, payload)
  },

  /** Odrzuca rezerwację wizyty z podaniem przyczyny. */
  rejectVisit(id: string, cancel_reason = '') {
    return api.post<Visit>(`/therapist/visits/${id}/reject/`, { cancel_reason })
  },

  /** Pobiera zdefiniowane typy i cennik usług terapeutycznych. */
  listTherapyTypes() {
    return listResults<TherapyType>('/therapist/therapy-types/')
  },

  /** Pobiera szablony/presety typów terapii. */
  listTherapyTypePresets() {
    return listResults<TherapyTypePreset>('/therapist/therapy-types/presets/')
  },

  /** Generuje domyślne typy terapii z presetów dla nowo zarejestrowanego fizjoterapeuty. */
  async seedTherapyTypePresets() {
    const page = await api.post<Paginated<TherapyType> | { results: TherapyType[] }>(
      '/therapist/therapy-types/seed-presets/',
      {},
    )
    return Array.isArray(page) ? page : page.results
  },

  /** Pobiera reguły dostępności czasowej fizjoterapeuty. */
  listAvailabilities() {
    return listResults<AvailabilitySlot>('/therapist/availabilities/')
  },

  /** Definiuje nową regułę lub grafik dostępności fizjoterapeuty. */
  createAvailability(payload: Partial<AvailabilitySlot>) {
    return api.post<AvailabilitySlot>('/therapist/availabilities/', payload)
  },

  /** Usuwa regułę dostępności czasowej. */
  deleteAvailability(id: string) {
    return api.delete(`/therapist/availabilities/${id}/`)
  },

  /** Pobiera publicznie dostępne wolne terminy dla pacjentów u wybranego fizjoterapeuty. */
  listPublicAvailableSlots(therapistId: string, dateIso?: string) {
    const query = dateIso ? `?date=${encodeURIComponent(dateIso)}` : ''
    return listResults<AvailabilitySlot>(`/therapists/${therapistId}/available-slots/${query}`)
  },

  /** Pobiera wolne terminy wraz ze szczegółowymi informacjami o długości i opcjach usługi. */
  listPublicAvailableSlotsWithDetails(therapistId: string, dateIso?: string) {
    const query = dateIso ? `?date=${encodeURIComponent(dateIso)}` : ''
    return api.get<AvailableSlotsResponse>(`/therapists/${therapistId}/available-slots/${query}`)
  },

  /** Pobiera listę świąt państwowych i dni ustawowo wolnych od pracy w Polsce. */
  listPolishHolidays(year?: number) {
    const query = year ? `?year=${year}` : ''
    return listResults<Holiday>(`/scheduling/holidays/${query}`)
  },
}
