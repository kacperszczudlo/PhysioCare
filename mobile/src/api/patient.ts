/**
 * @file patient.ts
 * @description Moduł API pacjenta – obsługa profilu, zgód, wizyt, ćwiczeń domowych, dokumentów medycznych oraz preferencji powiadomień Push.
 */

import { api } from './client'
import type {
  ClinicalDocumentItem,
  ClinicalDocumentKind,
  Consent,
  CreateReviewPayload,
  DeviceToken,
  ExerciseCompletion,
  ExercisePlanItem,
  MedicalDocument,
  NotificationPreference,
  Paginated,
  PatientDataExport,
  PatientProfile,
  RatingSummary,
  ReviewItem,
  TherapistPublic,
  TherapyType,
  TodayExercise,
  TreatmentEpisode,
  Visit,
  VisitRequestPayload,
} from './types'

/**
 * Pomocnicza funkcja rozpakowująca wyniki zapytania zwracającego tablicę bezpośrednią lub obiekt ze stronnicowaniem.
 *
 * @template T - Typ elementu listy.
 * @param data - Odpowiedź z serwera (tablica lub obiekt Paginated).
 * @returns Jednolita tablica elementów typu T.
 */
function unwrapList<T>(data: T[] | Paginated<T>): T[] {
  return Array.isArray(data) ? data : data.results
}

/**
 * Obiekt udostępniający metody API dedykowane zalogowanemu pacjentowi.
 */
export const patientApi = {
  /**
   * Pobiera pełny profil zalogowanego pacjenta.
   *
   * @returns Profil pacjenta.
   */
  getProfile() {
    return api.get<PatientProfile>('/me/profile/')
  },

  /**
   * Aktualizuje dane osobowe i kontaktowe w profilu pacjenta.
   *
   * @param payload - Częściowe dane profilu do aktualizacji (imię, nazwisko, PESEL, telefon).
   * @returns Zaktualizowany profil pacjenta.
   */
  updateProfile(
    payload: Partial<Pick<PatientProfile, 'first_name' | 'last_name' | 'pesel' | 'phone'>>,
  ) {
    return api.patch<PatientProfile>('/me/profile/', payload)
  },

  /**
   * Przesyła nowe zdjęcie profilowe (awatar) pacjenta.
   *
   * @param uri - Ścieżka lokalna pliku na urządzeniu mobilnym.
   * @param mimeType - Typ MIME obrazu (domyślnie 'image/jpeg').
   * @param fileName - Nazwa pliku (domyślnie 'avatar.jpg').
   * @returns Zaktualizowany profil z nowym adresem awatara.
   */
  uploadAvatar(uri: string, mimeType = 'image/jpeg', fileName = 'avatar.jpg') {
    const body = new FormData()
    body.append('file', {
      uri,
      type: mimeType,
      name: fileName,
    } as unknown as Blob)
    return api.post<PatientProfile>('/me/profile/avatar/', body)
  },

  /**
   * Pobiera listę udzielonych oraz opcjonalnych zgód pacjenta.
   *
   * @returns Lista zgód pacjenta.
   */
  async getConsents() {
    const data = await api.get<Consent[] | Paginated<Consent>>('/me/consents/')
    return unwrapList(data)
  },

  /**
   * Aktualizuje status opcjonalnych zgód (np. marketing, badania naukowe).
   *
   * @param payload - Obiekt ze statusami opcjonalnych zgód.
   * @returns Zaktualizowana lista zgód.
   */
  updateOptionalConsents(payload: { marketing?: boolean; research?: boolean }) {
    return api.patch<Consent[]>('/me/consents/optional/', payload)
  },

  /**
   * Zgłasza żądanie wyeksportowania pełnych danych osobowych i medycznych pacjenta.
   *
   * @returns Obiekt eksportu danych ze statusem oraz linkiem do pobrania.
   */
  requestDataExport() {
    return api.post<PatientDataExport>('/me/data-export/')
  },

  /**
   * Wnosi wniosek o usunięcie konta pacjenta z systemu PhysioCare.
   *
   * @param reason - Opcjonalny powód usunięcia konta podany przez pacjenta.
   * @returns Komunikat z potwierdzeniem przyjęcia zgłoszenia.
   */
  requestAccountDeletion(reason?: string) {
    return api.post<{ detail: string }>('/me/account-deletion-request/', {
      reason: reason ?? '',
    })
  },

  /**
   * Pobiera listę wizyt pacjenta przefiltrowaną po statusie czasowym.
   *
   * @param status - 'upcoming' (nadchodzące) lub 'past' (zakończone/historyczne).
   * @returns Lista wizyt.
   */
  async getVisits(status: 'upcoming' | 'past') {
    const data = await api.get<Visit[] | Paginated<Visit>>(`/me/visits/?status=${status}`)
    return unwrapList(data)
  },

  /**
   * Pobiera szczegółowe informacje o pojedynczej wizycie.
   *
   * @param id - Identifkator wizyty (UUID).
   * @returns Obiekt wizyty.
   */
  getVisit(id: string) {
    return api.get<Visit>(`/visits/${id}/`)
  },

  /**
   * Składa wniosek o nową rezerwację wizyty u wybranego fizjoterapeuty.
   *
   * @param payload - Dane wymagane do złożenia rezerwacji.
   * @returns Utworzona wizyta.
   */
  requestVisit(payload: VisitRequestPayload) {
    return api.post<Visit>('/me/visits/', payload)
  },

  /**
   * Pobiera rodzaje usług fizjoterapeutycznych (opcjonalnie filtrowane po fizjoterapeucie).
   *
   * @param therapist_id - Opcjonalne ID fizjoterapeuty.
   * @returns Lista dostępnych typów terapii.
   */
  async getTherapyTypes(therapist_id?: string) {
    const query = therapist_id ? `?therapist_id=${therapist_id}` : ''
    const data = await api.get<TherapyType[] | Paginated<TherapyType>>(`/me/therapy-types/${query}`)
    return unwrapList(data)
  },

  /**
   * Proponuje lub przeformatowuje godzinę/termin wizyty.
   *
   * @param id - Identyfikator wizyty.
   * @param payload - Nowy czas rozpoczęcia i zakończenia wizyty w formacie ISO.
   * @returns Zaktualizowany obiekt wizyty.
   */
  rescheduleVisit(id: string, payload: { start_at: string; end_at: string }) {
    return api.patch<Visit>(`/visits/${id}/reschedule/`, payload)
  },

  /**
   * Odwołuje zaplanowaną wizytę.
   *
   * @param id - Identyfikator wizyty.
   * @param cancel_reason - Powód odwołania wizyty.
   * @returns Wizyta ze statusem odwołania.
   */
  cancelVisit(id: string, cancel_reason = '') {
    return api.post<Visit>(`/visits/${id}/cancel/`, { cancel_reason })
  },

  /**
   * Pobiera listę ćwiczeń zaplanowanych na dzisiejszy dzień.
   *
   * @returns Lista dzisiejszych zadań treningowych.
   */
  async getExercisesToday() {
    const data = await api.get<TodayExercise[] | Paginated<TodayExercise>>('/me/exercises/today/')
    return unwrapList(data)
  },

  /**
   * Pobiera plan ćwiczeń w określonym zakresie.
   *
   * @param scope - 'all' (wszystkie), 'active' (aktywne), 'past' (zakończone).
   * @returns Lista pozycji planu ćwiczeń.
   */
  async getExercises(scope: 'all' | 'active' | 'past' = 'all') {
    const query = scope === 'all' ? '' : `?scope=${scope}`
    const data = await api.get<ExercisePlanItem[] | Paginated<ExercisePlanItem>>(
      `/me/exercises/${query}`,
    )
    return unwrapList(data)
  },

  /**
   * Pobiera listę epizodów leczenia pacjenta.
   *
   * @returns Lista epizodów terapeutycznych.
   */
  async getEpisodes() {
    const data = await api.get<TreatmentEpisode[] | Paginated<TreatmentEpisode>>('/me/episodes/')
    return unwrapList(data)
  },

  /**
   * Pobiera szczegóły danego epizodu leczenia.
   *
   * @param id - Identyfikator epizodu.
   * @returns Obiekt epizodu terapeutycznego.
   */
  getEpisode(id: string) {
    return api.get<TreatmentEpisode>(`/me/episodes/${id}/`)
  },

  /**
   * Oznacza wykonanie pojedynczego ćwiczenia z planu.
   *
   * @param assignment_id - Identyfikator przypisania ćwiczenia.
   * @param completed_on - Data wykonania ćwiczenia w formacie RRRR-MM-DD.
   * @param done - Statut zaliczenia ćwiczenia.
   * @returns Obiekt potwierdzenia wykonania ćwiczenia.
   */
  completeExercise(assignment_id: string, completed_on?: string, done = true) {
    return api.post<ExerciseCompletion>('/me/exercise-completions/', {
      assignment_id,
      done,
      ...(completed_on ? { completed_on } : {}),
    })
  },

  /**
   * Pobiera załączone pliki oraz dokumenty medyczne pacjenta.
   *
   * @returns Lista dokumentów.
   */
  async getDocuments() {
    const data = await api.get<MedicalDocument[] | Paginated<MedicalDocument>>('/me/documents/')
    return unwrapList(data)
  },

  /**
   * Pobiera wygenerowane kliniczne dokumenty medyczne (np. zalecenia, karty wizyt).
   *
   * @param kind - Opcjonalny typ dokumentu klinicznego.
   * @returns Lista dokumentów klinicznych.
   */
  async getClinicalDocuments(kind?: ClinicalDocumentKind) {
    const query = kind ? `?kind=${kind}` : ''
    const data = await api.get<{ count: number; results: ClinicalDocumentItem[] }>(
      `/me/clinical-documents/${query}`,
    )
    return data.results
  },

  /**
   * Pobiera publiczne dane wizytówkowe fizjoterapeuty.
   *
   * @param id - Identyfikator fizjoterapeuty.
   * @returns Publiczny profil fizjoterapeuty.
   */
  getTherapistPublic(id: string) {
    return api.get<TherapistPublic>(`/therapists/${id}/public/`)
  },

  /**
   * Pobiera ułożenie preferencji powiadomień pacjenta.
   *
   * @returns Lista ustawień powiadomień.
   */
  async getNotificationPreferences() {
    const data = await api.get<NotificationPreference[] | Paginated<NotificationPreference>>(
      '/me/notification-preferences/',
    )
    return unwrapList(data)
  },

  /**
   * Uaktualnia preferencje powiadomień pacjenta.
   *
   * @param preferences - Obiekt zawierający identyfikatory powiadomień i ich wartości boolowskie.
   * @returns Zaktualizowana lista preferencji.
   */
  updateNotificationPreferences(preferences: Record<string, boolean>) {
    return api.patch<NotificationPreference[]>('/me/notification-preferences/', {
      preferences,
    })
  },

  /**
   * Rejestruje token push urządzenia mobilnego w systemie powiadomień.
   *
   * @param expoPushToken - Unikalny token z usługi Expo Push Notifications.
   * @param platform - Platforma systemu operacyjnego ('ios' | 'android' | 'web' | 'unknown').
   * @returns Obiekt zarejestrowanego tokena.
   */
  registerDeviceToken(expoPushToken: string, platform: DeviceToken['platform'] = 'unknown') {
    return api.post<DeviceToken>('/me/device-tokens/', {
      expo_push_token: expoPushToken,
      platform,
    })
  },

  /**
   * Wyrejestrowuje token push urządzenia przy wylogowaniu.
   *
   * @param expoPushToken - Rejestrowany token urządzenia.
   */
  unregisterDeviceToken(expoPushToken: string) {
    return api.delete<void>('/me/device-tokens/', {
      body: { expo_push_token: expoPushToken },
    })
  },

  /**
   * Pobiera listę opinii dla danego fizjoterapeuty.
   *
   * @param therapistId - Identyfikator fizjoterapeuty.
   * @param rating - Opcjonalny filtr oceny (1-5).
   * @param ordering - Opcjonalny kierunek sortowania ('-created_at', '-rating', 'rating').
   */
  async getTherapistReviews(therapistId: string, rating?: number, ordering?: string) {
    const params = new URLSearchParams()
    if (rating) params.set('rating', String(rating))
    if (ordering) params.set('ordering', ordering)
    const query = params.toString() ? `?${params.toString()}` : ''
    const data = await api.get<ReviewItem[] | Paginated<ReviewItem>>(
      `/therapists/${therapistId}/reviews/${query}`,
    )
    return unwrapList(data)
  },

  /**
   * Pobiera podsumowanie ocen fizjoterapeuty (średnia, liczba, rozkład).
   *
   * @param therapistId - Identyfikator fizjoterapeuty.
   */
  getTherapistRatingSummary(therapistId: string) {
    return api.get<RatingSummary>(`/therapists/${therapistId}/rating-summary/`)
  },

  /**
   * Wystawia opinię bezpośrednio powiązaną z zakończoną wizytą.
   *
   * @param visitId - Identyfikator wizyty.
   * @param payload - Dane opinii (rating, comment, is_anonymous).
   */
  createVisitReview(visitId: string, payload: CreateReviewPayload) {
    return api.post<ReviewItem>(`/visits/${visitId}/review/`, payload)
  },

  /**
   * Wystawia opinię z profilu fizjoterapeuty (także poza wizytą lub z auto-powiązaniem).
   *
   * @param therapistId - Identyfikator fizjoterapeuty.
   * @param payload - Dane opinii.
   */
  createTherapistReview(therapistId: string, payload: CreateReviewPayload) {
    return api.post<ReviewItem>(`/therapists/${therapistId}/reviews/create/`, payload)
  },

  /**
   * Edytuje własną opinię w oknie 14 dni.
   *
   * @param reviewId - Identyfikator opinii.
   * @param payload - Nowe dane opinii.
   */
  editReview(reviewId: string, payload: CreateReviewPayload) {
    return api.patch<ReviewItem>(`/reviews/${reviewId}/edit/`, payload)
  },

  /**
   * Usuwa własną opinię.
   *
   * @param reviewId - Identyfikator opinii.
   */
  deleteReview(reviewId: string) {
    return api.delete<void>(`/reviews/${reviewId}/delete/`)
  },
}
