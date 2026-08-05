import { api } from './client'
import type {
  Exercise,
  ExerciseAssignment,
  ExerciseAssignmentPayload,
  ExerciseAssignmentUpdatePayload,
  ExerciseCategory,
  MediaType,
  Paginated,
} from './types'

async function listResults<T>(path: string): Promise<T[]> {
  const page = await api.get<Paginated<T> | T[]>(path)
  return Array.isArray(page) ? page : page.results
}

export interface ExerciseListParams {
  category?: string
  media_type?: MediaType | ''
  q?: string
}

export const exercisesApi = {
  listCategories() {
    return api.get<ExerciseCategory[]>('/therapist/exercise-categories/')
  },

  list(params: ExerciseListParams = {}) {
    const query = new URLSearchParams()
    if (params.category) {
      query.set('category', params.category)
    }
    if (params.media_type) {
      query.set('media_type', params.media_type)
    }
    if (params.q?.trim()) {
      query.set('q', params.q.trim())
    }
    const suffix = query.toString() ? `?${query.toString()}` : ''
    return listResults<Exercise>(`/therapist/exercises/${suffix}`)
  },

  create(formData: FormData) {
    return api.post<Exercise>('/therapist/exercises/', formData)
  },

  update(id: string, formData: FormData) {
    return api.patch<Exercise>(`/therapist/exercises/${id}/`, formData)
  },

  remove(id: string) {
    return api.delete<void>(`/therapist/exercises/${id}/`)
  },

  listAssignments(patientId: string, opts: { active?: boolean } = {}) {
    const query = new URLSearchParams({ patient: patientId })
    if (opts.active) {
      query.set('active', '1')
    }
    return listResults<ExerciseAssignment>(`/therapist/exercise-assignments/?${query}`)
  },

  assign(payload: ExerciseAssignmentPayload) {
    return api.post<ExerciseAssignment>('/therapist/exercise-assignments/', payload)
  },

  updateAssignment(id: string, payload: ExerciseAssignmentUpdatePayload) {
    return api.patch<ExerciseAssignment>(`/therapist/exercise-assignments/${id}/`, payload)
  },

  deleteAssignment(id: string) {
    return api.delete<void>(`/therapist/exercise-assignments/${id}/`)
  },
}
