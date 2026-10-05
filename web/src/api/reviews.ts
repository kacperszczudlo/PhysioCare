import { api } from './client'
import type { Paginated, RatingSummary, ReviewItem } from './types'

async function listResults<T>(path: string): Promise<T[]> {
  const page = await api.get<Paginated<T> | T[]>(path)
  return Array.isArray(page) ? page : page.results
}

/** Usługi API do pobierania opinii pacjentów oraz odpowiadania na nie przez fizjoterapeutę. */
export const reviewsApi = {
  /** Pobiera listę widocznych opinii danego fizjoterapeuty z opcjonalnym filtrem ocen i sortowaniem. */
  async listReviews(therapistId: string, rating?: number, ordering?: string): Promise<ReviewItem[]> {
    const params = new URLSearchParams()
    if (rating) params.set('rating', String(rating))
    if (ordering) params.set('ordering', ordering)
    const query = params.toString() ? `?${params.toString()}` : ''
    return listResults<ReviewItem>(`/therapists/${therapistId}/reviews/${query}`)
  },

  /** Pobiera statystyki ocen i podział na gwiazdki dla profilu fizjoterapeuty. */
  getRatingSummary(therapistId: string): Promise<RatingSummary> {
    return api.get<RatingSummary>(`/therapists/${therapistId}/rating-summary/`)
  },

  /** Dodaje lub edytuje odpowiedź fizjoterapeuty na opinię pacjenta. */
  replyToReview(reviewId: string, reply: string): Promise<ReviewItem> {
    return api.post<ReviewItem>(`/reviews/${reviewId}/reply/`, {
      therapist_reply: reply,
    })
  },
}
