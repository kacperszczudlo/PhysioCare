/**
 * @file phonePolicy.ts
 * @description Zasady walidacji oraz parsowania i formatowania numerów telefonów w standardzie międzynarodowym E.164.
 */

import {
  DEFAULT_COUNTRY_CODE,
  findCountryByDial,
  getCountryByCode,
  type CountryDial,
} from './countries'

/** Komunikaty błędów dotyczące numeru telefonu */
export const PHONE_MESSAGES = {
  required: 'Podaj numer telefonu.',
  invalid: 'Podaj prawidłowy numer telefonu (tylko cyfry numeru lokalnego).',
  tooLong: 'Numer telefonu może mieć co najwyżej 20 znaków.',
} as const

/** Struktura części składowych numeru telefonu */
export interface PhoneParts {
  /** Kod ISO kraju */
  countryCode: string
  /** Krajowy numer telefonu (bez kierunkowego) */
  nationalNumber: string
}

/** Zwraca obiekt domyślnego kraju (Polska) */
export function getDefaultCountry(): CountryDial {
  return getCountryByCode(DEFAULT_COUNTRY_CODE)!
}

/** Wyciąga z podanego ciągu znaków tylko cyfry */
export function digitsOnly(value: string): string {
  return value.replace(/\D+/g, '')
}

/**
 * Parsuje zapisany numer E.164 (np. +48123456789) na kod kraju oraz numer krajowy.
 *
 * @param value - Zapisany numer telefonu.
 * @returns Obiekt `PhoneParts`.
 */
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

/** Normalizuje krajowy numer telefonu, usuwając znaki niebędące cyframi */
export function normalizeNationalNumber(value: string): string {
  return digitsOnly(value)
}

/**
 * Waliduje krajowy numer telefonu przy podanym kodzie kraju.
 *
 * @param nationalNumber - Krajowy numer telefonu.
 * @param countryCode - Kod ISO kraju.
 * @param options - Opcja allowBlank pozwalająca na puste pole.
 * @returns Komunikat błędu po polsku lub null w przypadku sprawnego numeru.
 */
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

/**
 * Formatuje numer krajowy i kod kraju do pełnego ciągu E.164 akceptowanego przez backend API.
 *
 * @param nationalNumber - Krajowy numer telefonu.
 * @param countryCode - Kod ISO kraju.
 * @returns Sformatowany numer E.164 (np. "+48123456789") lub pusty ciąg.
 */
export function formatPhoneForApi(nationalNumber: string, countryCode: string): string {
  const national = normalizeNationalNumber(nationalNumber)
  if (!national) {
    return ''
  }
  const country = getCountryByCode(countryCode) ?? getDefaultCountry()
  return `+${country.dial}${national}`
}

