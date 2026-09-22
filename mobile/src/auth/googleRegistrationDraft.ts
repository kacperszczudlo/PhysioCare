/**
 * @file googleRegistrationDraft.ts
 * @description Moduł przekazywania danych tymczasowych z logowania Google do ekranu dokończenia rejestracji (gdy konto pacjenta jeszcze nie istnieje).
 */

/**
 * Szkic danych rejestracyjnych uzyskanych z usługi Google Sign-In.
 */
export type GoogleRegistrationDraft = {
  /** Token ID uzyskany z konta Google */
  credential: string
  /** Odczytany e-mail konta Google */
  email?: string
  /** Imię z profilu Google */
  first_name?: string
  /** Nazwisko z profilu Google */
  last_name?: string
}

let draft: GoogleRegistrationDraft | null = null

/**
 * Zapisuje szkic danych z logowania Google w pamięci RAM.
 *
 * @param next - Dane szkicu lub null do wyczyszczenia.
 */
export function setGoogleRegistrationDraft(next: GoogleRegistrationDraft | null) {
  draft = next
}

/**
 * Pobiera i jednocześnie czyści zapisany szkic danych rejestracyjnych Google.
 *
 * @returns Zapisany szkic lub null.
 */
export function takeGoogleRegistrationDraft(): GoogleRegistrationDraft | null {
  const current = draft
  draft = null
  return current
}

/**
 * Podgląda aktualnie zapisany szkic danych Google bez jego usuwania z pamięci.
 *
 * @returns Zapisany szkic lub null.
 */
export function peekGoogleRegistrationDraft(): GoogleRegistrationDraft | null {
  return draft
}

