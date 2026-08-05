import { api } from './client'
import type {
  BodyAreaPain,
  BodyViewSide,
  EpisodeStatus,
  Paginated,
  PatientDetail,
  PatientSummary,
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
    payload: { icd10_code?: string; summary_note?: string; status?: EpisodeStatus },
  ) {
    return api.post<TreatmentEpisode>(`/patients/${patientId}/episodes/`, payload)
  },

  updateEpisode(
    episodeId: string,
    payload: Partial<{
      icd10_code: string
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
}
