import { api } from './client'
import type {
  AdminDashboardStats,
  AdminReview,
  AdminSchedulingOverview,
  AdminTherapistStats,
  AdminUserDetail,
  AdminUserListItem,
  Paginated,
} from './types'

/** Parametry filtrowania listy użytkowników w panelu administratora. */
export interface AdminUsersFilterParams {
  role?: string
  is_active?: boolean
  email_verified?: boolean
  search?: string
  page?: number
}

/** Parametry filtrowania zbiorczego harmonogramu wizyt. */
export interface AdminSchedulingFilterParams {
  date_from?: string
  date_to?: string
  therapist_id?: string
}

/** Parametry filtrowania listy opinii pacjentów do moderacji. */
export interface AdminReviewsFilterParams {
  rating?: number
  is_visible?: boolean
  therapist_id?: string
  page?: number
}

/** Moduł komunikacji z endpointami administracyjnymi platformy PhysioCare. */
export const adminApi = {
  /** Pobiera zbiorcze metryki i analitykę KPI dla pulpitu administratora. */
  getDashboardStats(): Promise<AdminDashboardStats> {
    return api.get<AdminDashboardStats>('/admin/analytics/dashboard/')
  },

  /** Pobiera paginowaną listę użytkowników z opcjonalnymi filtrami i wyszukiwaniem. */
  getUsers(params?: AdminUsersFilterParams): Promise<Paginated<AdminUserListItem>> {
    const sp = new URLSearchParams()
    if (params?.role) sp.set('role', params.role)
    if (params?.is_active !== undefined) sp.set('is_active', String(params.is_active))
    if (params?.email_verified !== undefined) sp.set('email_verified', String(params.email_verified))
    if (params?.search) sp.set('search', params.search)
    if (params?.page) sp.set('page', String(params.page))
    const query = sp.toString() ? `?${sp.toString()}` : ''
    return api.get<Paginated<AdminUserListItem>>(`/admin/users/${query}`)
  },

  /** Pobiera szczegółowe dane pojedynczego użytkownika. */
  getUserDetail(userId: string): Promise<AdminUserDetail> {
    return api.get<AdminUserDetail>(`/admin/users/${userId}/`)
  },

  /** Włącza lub wyłącza blokadę konta użytkownika (is_active). */
  toggleUserStatus(userId: string, isActive: boolean): Promise<AdminUserDetail> {
    return api.patch<AdminUserDetail>(`/admin/users/${userId}/status/`, {
      is_active: isActive,
    })
  },

  /** Zleca wysłanie kodu resetowania hasła na adres e-mail użytkownika. */
  resetUserPassword(userId: string): Promise<{ message: string }> {
    return api.post<{ message: string }>(`/admin/users/${userId}/reset-password/`, {})
  },

  /** Zleca bezpieczną dezaktywację (soft-delete) konta użytkownika. */
  softDeleteUser(userId: string): Promise<{ message: string }> {
    return api.delete<{ message: string }>(`/admin/users/${userId}/`)
  },

  /** Pobiera zbiorczy harmonogram pracy wszystkich lub wybranego fizjoterapeuty. */
  getSchedulingOverview(params?: AdminSchedulingFilterParams): Promise<AdminSchedulingOverview> {
    const sp = new URLSearchParams()
    if (params?.date_from) sp.set('date_from', params.date_from)
    if (params?.date_to) sp.set('date_to', params.date_to)
    if (params?.therapist_id) sp.set('therapist_id', params.therapist_id)
    const query = sp.toString() ? `?${sp.toString()}` : ''
    return api.get<AdminSchedulingOverview>(`/admin/scheduling/overview/${query}`)
  },

  /** Pobiera statystyki efektywności i wizyt wszystkich fizjoterapeutów. */
  getTherapistStats(): Promise<AdminTherapistStats[]> {
    return api.get<AdminTherapistStats[]>('/admin/therapists/stats/')
  },

  /** Pobiera paginowaną listę opinii do celów moderacji. */
  getReviews(params?: AdminReviewsFilterParams): Promise<Paginated<AdminReview>> {
    const sp = new URLSearchParams()
    if (params?.rating) sp.set('rating', String(params.rating))
    if (params?.is_visible !== undefined) sp.set('is_visible', String(params.is_visible))
    if (params?.therapist_id) sp.set('therapist_id', params.therapist_id)
    if (params?.page) sp.set('page', String(params.page))
    const query = sp.toString() ? `?${sp.toString()}` : ''
    return api.get<Paginated<AdminReview>>(`/admin/reviews/${query}`)
  },

  /** Zmienia widoczność opinii (ukrycie moderacyjne / przywrócenie). */
  toggleReviewVisibility(reviewId: string, isVisible: boolean): Promise<AdminReview> {
    return api.patch<AdminReview>(`/admin/reviews/${reviewId}/visibility/`, {
      is_visible: isVisible,
    })
  },
}
