import {
  DEFAULT_COUNTRY_CODE,
  findCountryByDial,
  getCountryByCode,
  type CountryDial,
} from './countries'

export const PHONE_MESSAGES = {
  required: 'Podaj numer telefonu.',
  invalid: 'Podaj prawidłowy numer telefonu (tylko cyfry numeru lokalnego).',
  tooLong: 'Numer telefonu może mieć co najwyżej 20 znaków.',
} as const

export interface PhoneParts {
  countryCode: string
  nationalNumber: string
}

export function getDefaultCountry(): CountryDial {
  return getCountryByCode(DEFAULT_COUNTRY_CODE)!
}

export function digitsOnly(value: string): string {
  return value.replace(/\D+/g, '')
}

/** Split stored E.164 (+48123456789) into country + national number. */
export function parseStoredPhone(value: string | null | undefined): PhoneParts {
  const raw = (value ?? '').trim()
  if (!raw) {
    return { countryCode: DEFAULT_COUNTRY_CODE, nationalNumber: '' }
  }

  const digits = digitsOnly(raw)
  const country = findCountryByDial(digits) ?? getDefaultCountry()
  const national = digits.startsWith(country.dial) ? digits.slice(country.dial.length) : digits

  return { countryCode: country.code, nationalNumber: national }
}

export function normalizeNationalNumber(value: string): string {
  return digitsOnly(value)
}

export function getPhoneError(
  nationalNumber: string,
  countryCode: string,
  { allowBlank = true } = {},
): string | null {
  const national = normalizeNationalNumber(nationalNumber)
  if (!national) {
    return allowBlank ? null : PHONE_MESSAGES.required
  }

  const country = getCountryByCode(countryCode) ?? getDefaultCountry()
  const e164 = `+${country.dial}${national}`
  if (e164.length > 20) {
    return PHONE_MESSAGES.tooLong
  }

  // ITU E.164: country code + subscriber = max 15 digits total.
  const totalDigits = country.dial.length + national.length
  if (national.length < 4 || totalDigits > 15 || national.startsWith('0')) {
    return PHONE_MESSAGES.invalid
  }

  return null
}

export function formatPhoneForApi(nationalNumber: string, countryCode: string): string {
  const national = normalizeNationalNumber(nationalNumber)
  if (!national) {
    return ''
  }
  const country = getCountryByCode(countryCode) ?? getDefaultCountry()
  return `+${country.dial}${national}`
}
