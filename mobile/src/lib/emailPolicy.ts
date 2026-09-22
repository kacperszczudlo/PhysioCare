/**
 * @file emailPolicy.ts
 * @description Zasady walidacji oraz komunikaty błędów dotyczące formularzy wprowadzania adresu e-mail.
 */

/** Komunikaty błędów walidacji adresu e-mail */
export const EMAIL_MESSAGES = {
  required: 'Podaj adres e-mail.',
  invalid: 'Podaj prawidłowy adres e-mail (np. jan.kowalski@example.com).',
  tooLong: 'Adres e-mail może mieć co najwyżej 254 znaki.',
} as const

const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/

/**
 * Weryfikuje podany adres e-mail i zwraca komunikat błędu lub null, jeśli adres jest prawidłowy.
 *
 * @param email - Wprowadzony ciąg znaków reprezentujący e-mail.
 * @returns Komunikat błędu po polsku lub null w przypadku braku zastrzeżeń.
 */
export function getEmailError(email: string): string | null {
  const value = email.trim()
  if (!value) {
    return EMAIL_MESSAGES.required
  }
  if (value.length > 254) {
    return EMAIL_MESSAGES.tooLong
  }
  if (!EMAIL_PATTERN.test(value)) {
    return EMAIL_MESSAGES.invalid
  }
  return null
}

/**
 * Sprawdza, czy podany adres e-mail ma prawidłowy format syntaktyczny.
 *
 * @param email - Ciąg znaków do sprawdzenia.
 * @returns True jeśli adres jest poprawny.
 */
export function isValidEmail(email: string): boolean {
  return getEmailError(email) === null
}

