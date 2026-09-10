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

export const patientsApi = {
  list() {
    return listResults<PatientSummary>('/patients/')
  },

  get(id: string) {
    return api.get<PatientDetail>(`/patients/${id}/`)
  },
}

export const treatmentApi = {
  listEpisodes(patientId: string) {
    return listResults<TreatmentEpisode>(`/patients/${patientId}/episodes/`)
  },

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

  listBodyPain(episodeId: string) {
    return listResults<BodyAreaPain>(`/episodes/${episodeId}/body-pain/`)
  },

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

  deleteBodyPain(episodeId: string, entryId: string) {
    return api.delete<void>(`/episodes/${episodeId}/body-pain/${entryId}/`)
  },

  listNotes(episodeId: string) {
    return listResults<VisitNote>(`/episodes/${episodeId}/notes/`)
  },

  createNote(episodeId: string, content: string, visit?: string | null) {
    return api.post<VisitNote>(`/episodes/${episodeId}/notes/`, {
      content,
      visit: visit ?? null,
    })
  },

  listDiagnosticRecommendations(episodeId: string) {
    return listResults<DiagnosticRecommendation>(
      `/episodes/${episodeId}/diagnostic-recommendations/`,
    )
  },

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

  deleteDiagnosticRecommendation(episodeId: string, id: string) {
    return api.delete<void>(`/episodes/${episodeId}/diagnostic-recommendations/${id}/`)
  },

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

  listDeviceOrders(episodeId: string) {
    return listResults<MedicalDeviceOrder>(`/episodes/${episodeId}/device-orders/`)
  },

  createDeviceOrder(
    episodeId: string,
    payload: {
      device_code: string
      side?: BodySide
      quantity?: number
      icd10_code: string
      notes?: string
    },
  ) {
    return api.post<MedicalDeviceOrder>(`/episodes/${episodeId}/device-orders/`, payload)
  },

  deleteDeviceOrder(episodeId: string, id: string) {
    return api.delete<void>(`/episodes/${episodeId}/device-orders/${id}/`)
  },

  updateDeviceOrder(
    episodeId: string,
    id: string,
    payload: {
      device_code?: string
      side?: BodySide
      quantity?: number
      icd10_code?: string
      notes?: string
      status?: string
    },
  ) {
    return api.patch<MedicalDeviceOrder>(`/episodes/${episodeId}/device-orders/${id}/`, payload)
  },

  listOrderRefusals(episodeId: string) {
    return listResults<PhysicianOrderRefusal>(`/episodes/${episodeId}/order-refusals/`)
  },

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

  deleteOrderRefusal(episodeId: string, id: string) {
    return api.delete<void>(`/episodes/${episodeId}/order-refusals/${id}/`)
  },

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

  listReceptaNaRuch(patientId: string) {
    return listResults<ReceptaNaRuchReferral>(`/patients/${patientId}/recepta-na-ruch/`)
  },

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

  deleteReceptaNaRuch(patientId: string, id: string) {
    return api.delete<void>(`/patients/${patientId}/recepta-na-ruch/${id}/`)
  },

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

  getMedicalDeviceCatalog() {
    return api.get<MedicalDeviceCatalog>('/medical-devices/catalog/')
  },

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
