export const MIN_PASSWORD_LENGTH = 8

const SPECIAL_CHAR_PATTERN = /[^A-Za-z0-9_]/

export const PASSWORD_MESSAGES = {
  tooShort: `Hasło musi mieć co najmniej ${MIN_PASSWORD_LENGTH} znaków.`,
  entirelyNumeric: 'Hasło nie może składać się wyłącznie z cyfr.',
  noSpecial:
    'Hasło musi zawierać co najmniej jeden znak specjalny (np. ! @ # $ % & *).',
  tooSimilar: 'Hasło jest zbyt podobne do Twoich danych (e-mail, imię lub nazwisko).',
  mismatch: 'Hasła nie są identyczne.',
  required: 'Podaj hasło.',
} as const

export type PasswordRequirementId =
  | 'minLength'
  | 'notNumeric'
  | 'hasSpecial'
  | 'notSimilar'

export interface PasswordRequirement {
  id: PasswordRequirementId
  label: string
  met: boolean
}

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

export function hasSpecialCharacter(password: string): boolean {
  return SPECIAL_CHAR_PATTERN.test(password)
}

export function isPasswordTooSimilar(password: string, hints: PasswordUserHints): boolean {
  const pw = normalize(password)
  if (pw.length < 3) {
    return false
  }
  return attributeFragments(hints).some(
    (frag) => frag.length >= 3 && (pw.includes(frag) || frag.includes(pw)),
  )
}

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

export function getPasswordError(
  password: string,
  hints: PasswordUserHints = {},
): string | null {
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

export function passwordsMatch(password: string, confirm: string): boolean {
  return password.length > 0 && password === confirm
}
