/** Słownik komunikatów błędów walidacji numeru Prawa Wykonywania Zawodu Fizjoterapeuty (PWZF). */
export const PWZF_MESSAGES = {
  required: 'Podaj numer PWZFz.',
  invalid: 'Podaj prawidłowy numer PWZFz - dokładnie 5 cyfr (np. 12345).',
  tooLong: 'Numer PWZFz może mieć co najwyżej 20 znaków.',
} as const

const PREFIX_PATTERN = /^(?:pwzfz|pwzf)(?:\s*nr\.?|\s*nr|:|-)?\s*/i

/**
 * Normalizuje ciąg znaków numeru PWZF, usuwając potencjalne prefiksy (np. "PWZFz nr 71239" -> "71239").
 *
 * @param value - Surowy tekst wprowadzony przez fizjoterapeutę.
 * @returns 5-cyfrowy ciąg cyfr numeru PWZF.
 */
export function normalizePwzf(value: string): string {
  const withoutPrefix = value.trim().replace(PREFIX_PATTERN, '')
  return withoutPrefix.replace(/[\s-]/g, '')
}

/**
 * Waliduje numer Prawa Wykonywania Zawodu Fizjoterapeuty (KIF) pod kątem 5 cyfr po normalizacji.
 *
 * @param pwzf - Wprowadzony numer PWZF.
 * @returns Wiadomość błędu lub null przy poprawnym numerze.
 */
export function getPwzfError(pwzf: string): string | null {
  const raw = pwzf.trim()
  if (!raw) {
    return PWZF_MESSAGES.required
  }
  if (raw.length > 20) {
    return PWZF_MESSAGES.tooLong
  }
  const digits = normalizePwzf(raw)
  if (!/^\d{5}$/.test(digits)) {
    return PWZF_MESSAGES.invalid
  }
  return null
}
