/**
 * @file peselPolicy.ts
 * @description Zasady walidacji polskiego numeru PESEL (weryfikacja formatu 11 cyfr, dekodowanie daty urodzenia z uwzględnieniem stuleci oraz obliczanie sumy kontrolnej).
 */

/** Komunikaty błędów walidacji numeru PESEL */
export const PESEL_MESSAGES = {
  required: 'Podaj numer PESEL.',
  invalidFormat: 'PESEL musi składać się z dokładnie 11 cyfr.',
  invalidChecksum: 'Numer PESEL jest nieprawidłowy (błędna suma kontrolna).',
  invalidDate: 'Numer PESEL jest nieprawidłowy (błędna data urodzenia).',
  tooLong: 'Numer PESEL może mieć co najwyżej 11 znaków.',
} as const

const PESEL_WEIGHTS = [1, 3, 7, 9, 1, 3, 7, 9, 1, 3] as const

/** Dekoduje i weryfikuje poprawność daty urodzenia zapisanej w numerze PESEL */
function decodePeselBirthDate(digits: string): Date | null {
  const year = Number(digits.slice(0, 2))
  let month = Number(digits.slice(2, 4))
  const day = Number(digits.slice(4, 6))
  let century: number

  if (month >= 1 && month <= 12) {
    century = 1900
  } else if (month >= 21 && month <= 32) {
    century = 2000
    month -= 20
  } else if (month >= 41 && month <= 52) {
    century = 2100
    month -= 40
  } else if (month >= 61 && month <= 72) {
    century = 2200
    month -= 60
  } else if (month >= 81 && month <= 92) {
    century = 1800
    month -= 80
  } else {
    return null
  }

  const fullYear = century + year
  const date = new Date(Date.UTC(fullYear, month - 1, day))
  if (
    date.getUTCFullYear() !== fullYear ||
    date.getUTCMonth() !== month - 1 ||
    date.getUTCDate() !== day
  ) {
    return null
  }
  return date
}

/** Oblicza i sprawdza zgodność cyfry kontrolnej numeru PESEL */
function hasValidChecksum(digits: string): boolean {
  const total = PESEL_WEIGHTS.reduce(
    (sum, weight, index) => sum + weight * Number(digits[index]),
    0,
  )
  const control = (10 - (total % 10)) % 10
  return control === Number(digits[10])
}

/**
 * Weryfikuje poprawność 11-cyfrowego numeru PESEL.
 *
 * @param pesel - Numer PESEL w postaci ciągu cyfr.
 * @param options - Opcja allowBlank pozwalająca na puste pole.
 * @returns Komunikat błędu po polsku lub null w przypadku sprawnego numeru PESEL.
 */
export function getPeselError(pesel: string, { allowBlank = true } = {}): string | null {
  const value = pesel.trim()
  if (!value) {
    return allowBlank ? null : PESEL_MESSAGES.required
  }
  if (value.length > 11) {
    return PESEL_MESSAGES.tooLong
  }
  if (!/^\d{11}$/.test(value)) {
    return PESEL_MESSAGES.invalidFormat
  }
  if (!decodePeselBirthDate(value)) {
    return PESEL_MESSAGES.invalidDate
  }
  if (!hasValidChecksum(value)) {
    return PESEL_MESSAGES.invalidChecksum
  }
  return null
}
