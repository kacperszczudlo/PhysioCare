/**
 * @file passwordPolicy.ts
 * @description Zasady walidacji haseł użytkowników (wymogi długości, znaki specjalne, wykluczenie haseł numerycznych oraz podobieństwa do danych osobowych).
 */

/** Minimalna dopuszczalna długość hasła w znakach */
export const MIN_PASSWORD_LENGTH = 8

const SPECIAL_CHAR_PATTERN = /[^A-Za-z0-9_]/

/** Komunikaty błędów walidacji hasła w języku polskim */
export const PASSWORD_MESSAGES = {
  tooShort: `Hasło musi mieć co najmniej ${MIN_PASSWORD_LENGTH} znaków.`,
  entirelyNumeric: 'Hasło nie może składać się wyłącznie z cyfr.',
  noSpecial: 'Hasło musi zawierać co najmniej jeden znak specjalny (np. ! @ # $ % & *).',
  tooSimilar: 'Hasło jest zbyt podobne do Twoich danych (e-mail, imię lub nazwisko).',
  required: 'Podaj hasło.',
  mismatch: 'Hasła nie są identyczne.',
} as const

/** Identyfikatory poszczególnych reguł siły hasła */
export type PasswordRequirementId = 'minLength' | 'notNumeric' | 'hasSpecial' | 'notSimilar'

/** Struktura pojedynczego wymogu dotyczącego hasła z wskaźnikiem jego spełnienia */
export interface PasswordRequirement {
  id: PasswordRequirementId
  label: string
  met: boolean
}

/** Dane pomocnicze użytkownika służące do weryfikacji braku podobieństwa hasła */
export interface PasswordUserHints {
  email?: string
  firstName?: string
  lastName?: string
}

function normalize(value: string): string {
  return value.trim().toLowerCase()
}

function attributeFragments(hints: PasswordUserHints): string[] {
  const fragments: string[] = []
  const email = hints.email?.trim()
  if (email) {
    fragments.push(normalize(email))
    const local = email.split('@')[0]
    if (local && local.length >= 3) {
      fragments.push(normalize(local))
    }
  }
  for (const part of [hints.firstName, hints.lastName]) {
    const value = part?.trim()
    if (value && value.length >= 3) {
      fragments.push(normalize(value))
    }
  }
  return fragments
}

/**
 * Sprawdza, czy hasło zawiera co najmniej jeden znak specjalny.
 *
 * @param password - Wprowadzone hasło.
 * @returns True jeśli hasło zawiera znak specjalny.
 */
export function hasSpecialCharacter(password: string): boolean {
  return SPECIAL_CHAR_PATTERN.test(password)
}

/**
 * Sprawdza, czy wpisane hasło zawiera w sobie fragmenty e-maila, imienia lub nazwiska.
 *
 * @param password - Hasło do przetestowania.
 * @param hints - Dane profilowe użytkownika.
 * @returns True jeśli hasło jest zbyt podobne.
 */
export function isPasswordTooSimilar(password: string, hints: PasswordUserHints): boolean {
  const pw = normalize(password)
  if (pw.length < 3) {
    return false
  }
  return attributeFragments(hints).some(
    (frag) => frag.length >= 3 && (pw.includes(frag) || frag.includes(pw)),
  )
}

/**
 * Zwraca listę poszczególnych wymagań siły hasła ze statusem ich spełnienia.
 *
 * @param password - Testowane hasło.
 * @param hints - Opcjonalne dane użytkownika.
 * @returns Lista obiektów `PasswordRequirement`.
 */
export function getPasswordRequirements(
  password: string,
  hints: PasswordUserHints = {},
): PasswordRequirement[] {
  const requirements: PasswordRequirement[] = [
    {
      id: 'minLength',
      label: `Co najmniej ${MIN_PASSWORD_LENGTH} znaków`,
      met: password.length >= MIN_PASSWORD_LENGTH,
    },
    {
      id: 'notNumeric',
      label: 'Nie składa się wyłącznie z cyfr',
      met: password.length === 0 ? false : !/^\d+$/.test(password),
    },
    {
      id: 'hasSpecial',
      label: 'Zawiera znak specjalny (np. ! @ #)',
      met: password.length === 0 ? false : hasSpecialCharacter(password),
    },
  ]

  if (attributeFragments(hints).length > 0) {
    requirements.push({
      id: 'notSimilar',
      label: 'Różni się od e-maila i danych osobowych',
      met: password.length === 0 ? false : !isPasswordTooSimilar(password, hints),
    })
  }

  return requirements
}

/**
 * Zwraca opis pierwszego niespełnionego błędu polityki haseł.
 *
 * @param password - Wpisane hasło.
 * @param hints - Wskazówki danych osobowych.
 * @returns Komunikat błędu po polsku lub null w przypadku sprawnego hasła.
 */
export function getPasswordError(password: string, hints: PasswordUserHints = {}): string | null {
  if (!password) {
    return PASSWORD_MESSAGES.required
  }
  if (password.length < MIN_PASSWORD_LENGTH) {
    return PASSWORD_MESSAGES.tooShort
  }
  if (/^\d+$/.test(password)) {
    return PASSWORD_MESSAGES.entirelyNumeric
  }
  if (!hasSpecialCharacter(password)) {
    return PASSWORD_MESSAGES.noSpecial
  }
  if (isPasswordTooSimilar(password, hints)) {
    return PASSWORD_MESSAGES.tooSimilar
  }
  return null
}

/**
 * Sprawdza, czy podane dwa hasła są ze sobą tożsame.
 *
 * @param password - Pierwsze hasło.
 * @param confirm - Powtórzone nowe hasło.
 * @returns True jeśli hasła pasują do siebie.
 */
export function passwordsMatch(password: string, confirm: string): boolean {
  return password.length > 0 && password === confirm
}
