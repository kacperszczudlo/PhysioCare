/** Słownik komuniaków błędów walidacji adresu e-mail. */
export const EMAIL_MESSAGES = {
  required: 'Podaj adres e-mail.',
  invalid: 'Podaj prawidłowy adres e-mail (np. jan.kowalski@example.com).',
  tooLong: 'Adres e-mail może mieć co najwyżej 254 znaki.',
} as const

const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/

/**
 * Waliduje adres e-mail użytkownika pod kątem obecności, długości RFC 5322 oraz formatu syntaktycznego.
 *
 * @param email - Wprowadzony ciąg znaków adresu e-mail.
 * @returns Wiadomość błędu lub null, jeśli adres jest prawidłowy.
 *
 * @example
 * const error = getEmailError("jan.kowalski@domain.pl"); // returns null
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
