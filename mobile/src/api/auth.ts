/**
 * @file auth.ts
 * @description Moduł API do obsługi procesów uwierzytelniania, rejestracji, resetu hasła oraz weryfikacji e-mail pacjenta.
 */

import { api } from './client'
import { tokenStorage } from './tokenStorage'
import type { AuthResponse, User } from './types'

/**
 * Ładunek danych wymagany przy rejestracji konta pacjenta.
 */
export interface PatientRegisterPayload {
  /** Adres e-mail pacjenta (opcjonalny w przypadku rejestracji Google) */
  email?: string
  /** Hasło do nowego konta */
  password?: string
  /** Token tożsamości z usługi Google Sign-In */
  google_credential?: string
  /** Imię pacjenta */
  first_name?: string
  /** Nazwisko pacjenta */
  last_name?: string
  /** Identyfikator wybranego fizjoterapeuty (opcjonalny) */
  therapist_id?: string
  /** Numer telefonu kontaktowego */
  phone?: string
  /** Zgody prawne i medyczne wyrażone przez pacjenta */
  consents: {
    /** Akceptacja regulaminu serwisu */
    terms: boolean
    /** Zgoda na przetwarzanie danych medycznych */
    medical_data: boolean
  }
}

/**
 * Wynik operacji rejestracji pacjenta.
 */
export type RegisterResult =
  | { kind: 'authenticated'; user: User }
  | { kind: 'needs_email_verification'; email: string; detail: string }

/**
 * Ładunek danych wymagany do potwierdzenia resetu hasła po weryfikacji kodu.
 */
export interface PasswordResetConfirmPayload {
  /** Jednorazowy token resetujący zyskany po poprawnej weryfikacji kodu */
  reset_token: string
  /** Nowe hasło użytkownika */
  new_password: string
  /** Powtórzone nowe hasło */
  new_password_confirm: string
}

/**
 * Zapisuje tokeny dostępu oraz odświeżania w bezpiecznym magazynie i zwraca obiekt użytkownika.
 *
 * @param response - Odpowiedź z serwera zawierająca tokeny oraz profil użytkownika.
 * @returns Zwraca zalogowanego użytkownika.
 */
async function persistAuth(response: AuthResponse): Promise<User> {
  await tokenStorage.setTokens(response.access, response.refresh)
  return response.user
}

/**
 * Obiekt udostępniający metody API związane z autoryzacją konta pacjenta.
 */
export const authApi = {
  /**
   * Loguje użytkownika za pomocą adresu e-mail i hasła.
   *
   * @param email - Adres e-mail użytkownika.
   * @param password - Hasło użytkownika.
   * @returns Obiekt zalogowanego użytkownika.
   */
  async login(email: string, password: string) {
    const data = await api.post<AuthResponse>(
      '/auth/login/',
      { email, password },
      { auth: false, skipAuthRefresh: true },
    )
    return persistAuth(data)
  },

  /**
   * Loguje użytkownika z wykorzystaniem tokena tożsamości Google.
   *
   * @param credential - Token ID uzyskany z usługi Google Sign-In.
   * @returns Obiekt zalogowanego użytkownika.
   */
  async loginWithGoogle(credential: string) {
    const data = await api.post<AuthResponse>(
      '/auth/google/',
      { credential },
      { auth: false, skipAuthRefresh: true },
    )
    return persistAuth(data)
  },

  /**
   * Rejestruje nowe konto pacjenta.
   *
   * @param payload - Dane rejestracyjne pacjenta wraz ze zgodami.
   * @returns Wynik rejestracji (zalogowany użytkownik lub wymagana weryfikacja e-mail).
   */
  async registerPatient(payload: PatientRegisterPayload): Promise<RegisterResult> {
    const data = await api.post<
      AuthResponse | { needs_email_verification?: boolean; email?: string; detail?: string }
    >('/auth/register/patient/', payload, {
      auth: false,
      skipAuthRefresh: true,
    })
    if (data && 'needs_email_verification' in data && data.needs_email_verification) {
      return {
        kind: 'needs_email_verification',
        email: typeof data.email === 'string' ? data.email : '',
        detail: typeof data.detail === 'string' ? data.detail : 'Sprawdź e-mail i wpisz kod.',
      }
    }
    if (data && 'user' in data && data.user) {
      const user = await persistAuth(data as AuthResponse)
      return { kind: 'authenticated', user }
    }
    throw new Error('Nieoczekiwana odpowiedź rejestracji.')
  },

  /**
   * Weryfikuje kod przesłany na adres e-mail po rejestracji.
   *
   * @param email - Adres e-mail użytkownika.
   * @param code - Jednorazowy kod weryfikacyjny z wiadomości e-mail.
   * @returns Obiekt zalogowanego użytkownika.
   */
  async verifyEmail(email: string, code: string) {
    const data = await api.post<AuthResponse>(
      '/auth/email/verify/',
      { email, code },
      { auth: false, skipAuthRefresh: true },
    )
    return persistAuth(data)
  },

  /**
   * Ponownie wysyła kod weryfikacyjny na podany adres e-mail.
   *
   * @param email - Adres e-mail użytkownika.
   * @returns Obiekt z komunikatem potwiedzającym wysłanie wiadomości.
   */
  resendEmailCode(email: string) {
    return api.post<{ detail: string }>(
      '/auth/email/resend/',
      { email },
      { auth: false, skipAuthRefresh: true },
    )
  },

  /**
   * Wysyła prośbę o zresetowanie hasła dla podanego adresu e-mail.
   *
   * @param email - Adres e-mail powiązany z kontem.
   * @returns Komunikat informacyjny z serwera.
   */
  requestPasswordReset(email: string) {
    return api.post<{ detail: string }>(
      '/auth/password-reset/request/',
      { email, client: 'mobile' },
      { auth: false, skipAuthRefresh: true },
    )
  },

  /**
   * Weryfikuje kod resetujący hasło i zwraca tymczasowy token resetujący.
   *
   * @param email - Adres e-mail użytkownika.
   * @param code - Kod weryfikacyjny z e-maila.
   * @returns Obiekt zawierający komunikat oraz reset_token.
   */
  verifyPasswordResetCode(email: string, code: string) {
    return api.post<{ detail: string; reset_token: string }>(
      '/auth/password-reset/verify/',
      { email, code },
      { auth: false, skipAuthRefresh: true },
    )
  },

  /**
   * Potwierdza zmianę hasła na podstawie tokena resetującego.
   *
   * @param payload - Obiekt zawierający reset_token oraz nowe hasło.
   * @returns Komunikat potwierdzający zmianę hasła.
   */
  confirmPasswordReset(payload: PasswordResetConfirmPayload) {
    return api.post<{ detail: string }>('/auth/password-reset/confirm/', payload, {
      auth: false,
      skipAuthRefresh: true,
    })
  },

  /**
   * Wylogowuje użytkownika, unieważniając token refresh i czyszcząc magazyn lokalny.
   */
  async logout() {
    try {
      const refresh = await tokenStorage.getRefresh()
      await api.post<{ detail: string }>('/auth/logout/', refresh ? { refresh } : {}, {
        skipAuthRefresh: true,
      })
    } finally {
      await tokenStorage.clear()
    }
  },

  /**
   * Zmienia hasło zalogowanego użytkownika.
   *
   * @param current_password - Dotychczasowe hasło.
   * @param new_password - Nowe hasło.
   * @returns Odpowiedź z serwera.
   */
  changePassword(current_password: string, new_password: string) {
    return api.post<{ detail: string }>('/auth/password-change/', {
      current_password,
      new_password,
    })
  },
}
