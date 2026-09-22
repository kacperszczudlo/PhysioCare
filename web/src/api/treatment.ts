import { api } from './client'
import type {
  BodyAreaPain,
  BodySide,
  BodyViewSide,
  DiagnosticRecommendation,
  EpisodeStatus,
  FundingHint,
  MedicalDeviceCatalog,
  MedicalDeviceOrder,
  Paginated,
  PatientDetail,
  PatientSummary,
  PhysicianOrderRefusal,
  ReceptaNaRuchReferral,
  RecommendationType,
  TreatmentEpisode,
  VisitNote,
} from './types'

async function listResults<T>(path: string): Promise<T[]> {
  const page = await api.get<Paginated<T> | T[]>(path)
  return Array.isArray(page) ? page : page.results
}

/** Usługi API do pobierania listy i kartoteki pacjentów fizjoterapeuty. */
export const patientsApi = {
  /** Pobiera podsumowującą listę pacjentów pod opieką fizjoterapeuty. */
  list() {
    return listResults<PatientSummary>('/patients/')
  },

  /** Pobiera pełne dane kartoteki pacjenta (historia, profil, wywiady). */
  get(id: string) {
    return api.get<PatientDetail>(`/patients/${id}/`)
  },
}

/** Usługi API do zarządzania epizodami leczenia, mapami bólu VAS, zaleceniami i wyrobami medycznymi NFZ. */
export const treatmentApi = {
  /** Pobiera historię epizodów terapeutycznych pacjenta. */
  listEpisodes(patientId: string) {
    return listResults<TreatmentEpisode>(`/patients/${patientId}/episodes/`)
  },

  /** Tworzy nowy epizod leczenia (diagnoza funkcjonalna, kod ICD-10). */
  createEpisode(
    patientId: string,
    payload: {
      icd10_code?: string
      functional_diagnosis?: string
      summary_note?: string
      status?: EpisodeStatus
    },
  ) {
    return api.post<TreatmentEpisode>(`/patients/${patientId}/episodes/`, payload)
  },

  /** Aktualizuje stan lub kod ICD-10 epizodu terapeutycznego. */
  updateEpisode(
    episodeId: string,
    payload: Partial<{
      icd10_code: string
      functional_diagnosis: string
      status: EpisodeStatus
      summary_note: string
      ended_at: string | null
    }>,
  ) {
    return api.patch<TreatmentEpisode>(`/episodes/${episodeId}/`, payload)
  },

  /** Pobiera punkty bolesności i natężenie bólu w skali VAS dla danego epizodu. */
  listBodyPain(episodeId: string) {
    return listResults<BodyAreaPain>(`/episodes/${episodeId}/body-pain/`)
  },

  /** Zapisuje nowy punkt mapy bólu (region ciała, strona, skala VAS 0-10, charakter bólu). */
  createBodyPain(
    episodeId: string,
    payload: {
      body_region: string
      view_side: BodyViewSide
      vas_score: number
      pain_character: string[]
      treatment_targets?: string[]
    },
  ) {
    return api.post<BodyAreaPain>(`/episodes/${episodeId}/body-pain/`, payload)
  },

  /** Aktualizuje ocenę bólu VAS lub cele terapeutyczne w danym punkcie. */
  updateBodyPain(
    episodeId: string,
    entryId: string,
    payload: {
      body_region?: string
      view_side?: BodyViewSide
      vas_score?: number
      pain_character?: string[]
      treatment_targets?: string[]
    },
  ) {
    return api.patch<BodyAreaPain>(`/episodes/${episodeId}/body-pain/${entryId}/`, payload)
  },

  /** Usuwa wpis natężenia bólu. */
  deleteBodyPain(episodeId: string, entryId: string) {
    return api.delete<void>(`/episodes/${episodeId}/body-pain/${entryId}/`)
  },

  /** Pobiera notatki terapeutyczne przypisane do epizodu. */
  listNotes(episodeId: string) {
    return listResults<VisitNote>(`/episodes/${episodeId}/notes/`)
  },

  /** Dodaje nową notatkę z wizyty lub konsultacji. */
  createNote(episodeId: string, content: string, visit?: string | null) {
    return api.post<VisitNote>(`/episodes/${episodeId}/notes/`, {
      content,
      visit: visit ?? null,
    })
  },

  /** Pobiera listę sugerowanych badań diagnostycznych (np. RTG, USG, MRI). */
  listDiagnosticRecommendations(episodeId: string) {
    return listResults<DiagnosticRecommendation>(
      `/episodes/${episodeId}/diagnostic-recommendations/`,
    )
  },

  /** Dodaje rekomendację badań diagnostycznych z uzasadnieniem i czerwonymi flagami. */
  createDiagnosticRecommendation(
    episodeId: string,
    payload: {
      recommendation_type: RecommendationType
      target_specialty?: string
      body_area?: string
      justification: string
      red_flags_noted?: boolean
      funding_hint?: FundingHint
    },
  ) {
    return api.post<DiagnosticRecommendation>(
      `/episodes/${episodeId}/diagnostic-recommendations/`,
      payload,
    )
  },

  /** Usuwa rekomendację diagnostyczną. */
  deleteDiagnosticRecommendation(episodeId: string, id: string) {
    return api.delete<void>(`/episodes/${episodeId}/diagnostic-recommendations/${id}/`)
  },

  /** Aktualizuje rekomendację diagnostyczną. */
  updateDiagnosticRecommendation(
    episodeId: string,
    id: string,
    payload: {
      recommendation_type?: RecommendationType
      target_specialty?: string
      body_area?: string
      justification?: string
      red_flags_noted?: boolean
      funding_hint?: FundingHint
    },
  ) {
    return api.patch<DiagnosticRecommendation>(
      `/episodes/${episodeId}/diagnostic-recommendations/${id}/`,
      payload,
    )
  },

  /** Pobiera zamówienia na wyroby medyczne NFZ w ramach epizodu. */
  listDeviceOrders(episodeId: string) {
    return listResults<MedicalDeviceOrder>(`/episodes/${episodeId}/device-orders/`)
  },

  /** Tworzy nowe zlecenie na wyrób medyczny (ortoza, wózek, kule) z kodem NFZ. */
  createDeviceOrder(
    episodeId: string,
    payload: {
      device_code: string
      side?: BodySide
      quantity?: number
      icd10_code: string
      access_code?: string
      notes?: string
    },
  ) {
    return api.post<MedicalDeviceOrder>(`/episodes/${episodeId}/device-orders/`, payload)
  },

  /** Usuwa zlecenie na wyrób medyczny. */
  deleteDeviceOrder(episodeId: string, id: string) {
    return api.delete<void>(`/episodes/${episodeId}/device-orders/${id}/`)
  },

  /** Aktualizuje status lub szczegóły zlecenia na wyrób medyczny. */
  updateDeviceOrder(
    episodeId: string,
    id: string,
    payload: {
      device_code?: string
      side?: BodySide
      quantity?: number
      icd10_code?: string
      access_code?: string
      notes?: string
      status?: string
    },
  ) {
    return api.patch<MedicalDeviceOrder>(`/episodes/${episodeId}/device-orders/${id}/`, payload)
  },

  /** Pobiera wpisy o odmowie wykonania zlecenia lekarskiego niebezpiecznego dla pacjenta. */
  listOrderRefusals(episodeId: string) {
    return listResults<PhysicianOrderRefusal>(`/episodes/${episodeId}/order-refusals/`)
  },

  /** Zapisuje uzasadnioną odmowę wykonania niewłaściwego zlecenia lekarskiego. */
  createOrderRefusal(
    episodeId: string,
    payload: {
      physician_order_description: string
      refusal_reason: string
      physician_notified?: boolean
    },
  ) {
    return api.post<PhysicianOrderRefusal>(`/episodes/${episodeId}/order-refusals/`, payload)
  },

  /** Usuwa wpis odmowy zlecenia lekarskiego. */
  deleteOrderRefusal(episodeId: string, id: string) {
    return api.delete<void>(`/episodes/${episodeId}/order-refusals/${id}/`)
  },

  /** Aktualizuje opis lub powód odmowy zlecenia lekarskiego. */
  updateOrderRefusal(
    episodeId: string,
    id: string,
    payload: {
      physician_order_description?: string
      refusal_reason?: string
      physician_notified?: boolean
    },
  ) {
    return api.patch<PhysicianOrderRefusal>(`/episodes/${episodeId}/order-refusals/${id}/`, payload)
  },

  /** Pobiera skierowania „Recepta na Ruch” dla pacjenta. */
  listReceptaNaRuch(patientId: string) {
    return listResults<ReceptaNaRuchReferral>(`/patients/${patientId}/recepta-na-ruch/`)
  },

  /** Tworzy skierowanie w programie „Recepta na Ruch”. */
  createReceptaNaRuch(
    patientId: string,
    payload: {
      readiness_confirmed: boolean
      activity_notes?: string
      episode?: string | null
    },
  ) {
    return api.post<ReceptaNaRuchReferral>(`/patients/${patientId}/recepta-na-ruch/`, payload)
  },

  /** Usuwa skierowanie z programu „Recepta na Ruch”. */
  deleteReceptaNaRuch(patientId: string, id: string) {
    return api.delete<void>(`/patients/${patientId}/recepta-na-ruch/${id}/`)
  },

  /** Aktualizuje status lub notatki skierowania „Recepta na Ruch”. */
  updateReceptaNaRuch(
    patientId: string,
    id: string,
    payload: {
      readiness_confirmed?: boolean
      activity_notes?: string
      episode?: string | null
      status?: string
    },
  ) {
    return api.patch<ReceptaNaRuchReferral>(
      `/patients/${patientId}/recepta-na-ruch/${id}/`,
      payload,
    )
  },

  /** Pobiera oficjalny słownik wyrobów medycznych NFZ z grupami i limitami dofinansowania. */
  getMedicalDeviceCatalog() {
    return api.get<MedicalDeviceCatalog>('/medical-devices/catalog/')
  },

  /** Wysyła dokument medyczny (PDF, zdjęcie RTG) dla pacjenta w FormData. */
  uploadDocument(payload: {
    patientId: string
    title: string
    file: File
    episodeId?: string | null
  }) {
    const body = new FormData()
    body.append('patient_id', payload.patientId)
    body.append('title', payload.title)
    body.append('file', payload.file)
    if (payload.episodeId) {
      body.append('episode_id', payload.episodeId)
    }
    return api.post<{
      id: string
      title: string
      file_url: string
      mime_type: string
      created_at: string
    }>('/therapist/documents/', body)
  },
}
