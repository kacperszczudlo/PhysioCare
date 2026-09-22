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

/** Parametry wyszukiwania i filtrowania katalogu ćwiczeń fizjoterapeutycznych. */
export interface ExerciseListParams {
  /** Identyfikator lub kod kategorii ćwiczenia. */
  category?: string
  /** Typ/rodzaj ćwiczenia. */
  type?: string
  /** Region/okolica ciała. */
  region?: string
  /** Grupa mięśniowa zaangażowana w ćwiczenie. */
  muscle?: string
  /** Wskazany uraz / schorzenie. */
  injury?: string
  /** Filtrowanie według typu załącznika (wideo, instrukcja obrazkowa). */
  media_type?: MediaType | ''
  /** Zapytanie tekstowe szukające w nazwie i opisie ćwiczenia. */
  q?: string
  /** Rodzaj kategorii (np. anatomia, typ ruchu). */
  kind?: CategoryKind
  /** Numer strony dla wyników stronnicowanych. */
  page?: number
}

/** Usługi API do zarządzania słownikiem ćwiczeń oraz przypisywaniem ich pacjentom. */
export const exercisesApi = {
  /** Pobiera słownik kategorii ćwiczeń. */
  listCategories(kind?: CategoryKind) {
    const suffix = kind ? `?kind=${kind}` : ''
    return api.get<ExerciseCategory[]>(`/therapist/exercise-categories/${suffix}`)
  },

  /** Wyszukuje i pobiera listę ćwiczeń z opcjonalnym stronnicowaniem i filtrami. */
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
    return api
      .get<Paginated<Exercise> | Exercise[]>(`/therapist/exercises/${suffix}`)
      .then((page) => {
        if (Array.isArray(page)) {
          return { count: page.length, next: null, previous: null, results: page }
        }
        return page
      })
  },

  /** Tworzy nowe ćwiczenie wraz z opcjonalnym plikiem wideo/grafiki w FormData. */
  create(formData: FormData) {
    return api.post<Exercise>('/therapist/exercises/', formData)
  },

  /** Aktualizuje istniejące ćwiczenie. */
  update(id: string, formData: FormData) {
    return api.patch<Exercise>(`/therapist/exercises/${id}/`, formData)
  },

  /** Usuwa ćwiczenie o podanym identyfikatorze. */
  remove(id: string) {
    return api.delete<void>(`/therapist/exercises/${id}/`)
  },

  /** Pobiera zestaw ćwiczeń przypisanych danemu pacjentowi. */
  listAssignments(patientId: string, opts: { active?: boolean } = {}) {
    const query = new URLSearchParams({ patient: patientId })
    if (opts.active) {
      query.set('active', '1')
    }
    return listResults<ExerciseAssignment>(`/therapist/exercise-assignments/?${query}`)
  },

  /** Przypisuje nowe ćwiczenie pacjentowi z wyznaczonym dawkowaniem i instrukcją. */
  assign(payload: ExerciseAssignmentPayload) {
    return api.post<ExerciseAssignment>('/therapist/exercise-assignments/', payload)
  },

  /** Aktualizuje dawkowanie lub status przypisanego ćwiczenia. */
  updateAssignment(id: string, payload: ExerciseAssignmentUpdatePayload) {
    return api.patch<ExerciseAssignment>(`/therapist/exercise-assignments/${id}/`, payload)
  },

  /** Usuwa przypisanie ćwiczenia dla pacjenta. */
  deleteAssignment(id: string) {
    return api.delete<void>(`/therapist/exercise-assignments/${id}/`)
  },
}
