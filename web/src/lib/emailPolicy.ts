/** Client-side email validation — aligned with backend accounts.email_policy. */

export const EMAIL_MESSAGES = {
  required: 'Podaj adres e-mail.',
  invalid: 'Podaj prawidłowy adres e-mail (np. jan.kowalski@example.com).',
  tooLong: 'Adres e-mail może mieć co najwyżej 254 znaki.',
} as const

/** Practical format check (not a full RFC parser). */
const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/

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
