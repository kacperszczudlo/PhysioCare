export const PHONE_MESSAGES = {
  required: 'Podaj numer telefonu.',
  invalid:
    'Podaj prawidłowy polski numer telefonu (9 cyfr, opcjonalnie z numerem kierunkowym +48).',
  tooLong: 'Numer telefonu może mieć co najwyżej 20 znaków.',
} as const

export function normalizePhone(value: string): string {
  let digits = value.replace(/\D+/g, '')
  if (digits.startsWith('0048')) {
    digits = digits.slice(4)
  } else if (digits.startsWith('48') && digits.length === 11) {
    digits = digits.slice(2)
  } else if (digits.startsWith('0') && digits.length === 10) {
    digits = digits.slice(1)
  }
  return digits
}

export function getPhoneError(phone: string, { allowBlank = true } = {}): string | null {
  const raw = phone.trim()
  if (!raw) {
    return allowBlank ? null : PHONE_MESSAGES.required
  }
  if (raw.length > 20) {
    return PHONE_MESSAGES.tooLong
  }
  const digits = normalizePhone(raw)
  if (digits.length !== 9 || digits[0] === '0') {
    return PHONE_MESSAGES.invalid
  }
  return null
}

export function formatPhoneForApi(phone: string): string {
  const raw = phone.trim()
  if (!raw) {
    return ''
  }
  return `+48${normalizePhone(raw)}`
}
