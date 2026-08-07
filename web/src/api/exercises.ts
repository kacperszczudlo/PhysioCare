import { api } from './client'
import type {
  CategoryKind,
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
  type?: string
  region?: string
  muscle?: string
  injury?: string
  media_type?: MediaType | ''
  q?: string
  kind?: CategoryKind
  page?: number
}

export const exercisesApi = {
  listCategories(kind?: CategoryKind) {
    const suffix = kind ? `?kind=${kind}` : ''
    return api.get<ExerciseCategory[]>(`/therapist/exercise-categories/${suffix}`)
  },

  list(params: ExerciseListParams = {}) {
    const query = new URLSearchParams()
    for (const key of ['category', 'type', 'region', 'muscle', 'injury'] as const) {
      const value = params[key]
      if (value) {
        query.set(key, value)
      }
    }
    if (params.media_type) {
      query.set('media_type', params.media_type)
    }
    if (params.q?.trim()) {
      query.set('q', params.q.trim())
    }
    if (params.page && params.page > 1) {
      query.set('page', String(params.page))
    }
    const suffix = query.toString() ? `?${query.toString()}` : ''
    return api.get<Paginated<Exercise> | Exercise[]>(`/therapist/exercises/${suffix}`).then((page) => {
      if (Array.isArray(page)) {
        return { count: page.length, next: null, previous: null, results: page }
      }
      return page
    })
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
