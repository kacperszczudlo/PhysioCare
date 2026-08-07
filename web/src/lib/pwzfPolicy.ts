export const PWZF_MESSAGES = {
  required: 'Podaj numer PWZFz.',
  invalid: 'Podaj prawidłowy numer PWZFz — dokładnie 5 cyfr (np. 12345).',
  tooLong: 'Numer PWZFz może mieć co najwyżej 20 znaków.',
} as const

const PREFIX_PATTERN = /^(?:pwzfz|pwzf)(?:\s*nr\.?|\s*nr|:|-)?\s*/i

export function normalizePwzf(value: string): string {
  const withoutPrefix = value.trim().replace(PREFIX_PATTERN, '')
  return withoutPrefix.replace(/[\s-]/g, '')
}

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
