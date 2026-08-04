import { api } from './client'
import type {
  Exercise,
  ExerciseAssignment,
  ExerciseAssignmentPayload,
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

  assign(payload: ExerciseAssignmentPayload) {
    return api.post<ExerciseAssignment>('/therapist/exercise-assignments/', payload)
  },
}
