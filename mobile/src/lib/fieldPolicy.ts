export const NAME_MESSAGES = {
  firstRequired: 'Podaj imię.',
  lastRequired: 'Podaj nazwisko.',
  firstTooShort: 'Imię musi mieć co najmniej 2 znaki.',
  lastTooShort: 'Nazwisko musi mieć co najmniej 2 znaki.',
  firstTooLong: 'Imię może mieć co najwyżej 100 znaków.',
  lastTooLong: 'Nazwisko może mieć co najwyżej 100 znaków.',
  firstInvalid:
    "Imię może zawierać litery, spacje, myślnik i apostrof (np. Anna, Jean-Pierre, O'Brien).",
  lastInvalid:
    'Nazwisko może zawierać litery, spacje, myślnik i apostrof (np. Kowalska, Nowak-Wiśniewska).',
} as const

const NAME_PATTERN =
  /^[A-Za-zÀ-ÖØ-öø-ÿĄąĆćĘęŁłŃńÓóŚśŹźŻż]+(?:[ '\-][A-Za-zÀ-ÖØ-öø-ÿĄąĆćĘęŁłŃńÓóŚśŹźŻż]+)*$/

function normalizeName(value: string): string {
  return value.trim().replace(/\s+/g, ' ')
}

export function getFirstNameError(value: string): string | null {
  const name = normalizeName(value)
  if (!name) {
    return NAME_MESSAGES.firstRequired
  }
  if (name.length < 2) {
    return NAME_MESSAGES.firstTooShort
  }
  if (name.length > 100) {
    return NAME_MESSAGES.firstTooLong
  }
  if (!NAME_PATTERN.test(name)) {
    return NAME_MESSAGES.firstInvalid
  }
  return null
}

export function getLastNameError(value: string): string | null {
  const name = normalizeName(value)
  if (!name) {
    return NAME_MESSAGES.lastRequired
  }
  if (name.length < 2) {
    return NAME_MESSAGES.lastTooShort
  }
  if (name.length > 100) {
    return NAME_MESSAGES.lastTooLong
  }
  if (!NAME_PATTERN.test(name)) {
    return NAME_MESSAGES.lastInvalid
  }
  return null
}

export const FIELD_MESSAGES = {
  addressTooShort: 'Adres jest zbyt krótki — podaj ulicę i miejscowość.',
  addressTooLong: 'Adres może mieć co najwyżej 300 znaków.',
  bioTooLong: 'Opis profilu może mieć co najwyżej 2000 znaków.',
  courseRequired: 'Nazwa kursu nie może być pusta.',
  courseTooLong: 'Nazwa kursu może mieć co najwyżej 200 znaków.',
  icd10Invalid: 'Podaj prawidłowy kod ICD-10 (np. M54.5, S83.4) albo pozostaw puste.',
  dosageRequired: 'Podaj dawkowanie ćwiczenia.',
  dosageTooLong: 'Dawkowanie może mieć co najwyżej 100 znaków.',
  titleRequired: 'Podaj tytuł ćwiczenia.',
  titleTooLong: 'Tytuł może mieć co najwyżej 200 znaków.',
  noteRequired: 'Treść notatki nie może być pusta.',
} as const

const ICD10_PATTERN = /^[A-TV-Z][0-9]{2}(?:\.[0-9A-TV-Z]{1,4})?$/i

export function getAddressError(value: string, { allowBlank = true } = {}): string | null {
  const address = value.trim().replace(/\s+/g, ' ')
  if (!address) {
    return allowBlank ? null : 'Podaj adres.'
  }
  if (address.length < 5) {
    return FIELD_MESSAGES.addressTooShort
  }
  if (address.length > 300) {
    return FIELD_MESSAGES.addressTooLong
  }
  return null
}

export function getBioError(value: string): string | null {
  if (value.trim().length > 2000) {
    return FIELD_MESSAGES.bioTooLong
  }
  return null
}

export function getCourseError(value: string): string | null {
  const course = value.trim().replace(/\s+/g, ' ')
  if (!course) {
    return FIELD_MESSAGES.courseRequired
  }
  if (course.length > 200) {
    return FIELD_MESSAGES.courseTooLong
  }
  return null
}

export function getIcd10Error(value: string, { allowBlank = true } = {}): string | null {
  const code = value.trim()
  if (!code) {
    return allowBlank ? null : 'Podaj kod ICD-10.'
  }
  if (code.length > 10 || !ICD10_PATTERN.test(code)) {
    return FIELD_MESSAGES.icd10Invalid
  }
  return null
}

export function getDosageError(value: string): string | null {
  const dosage = value.trim()
  if (!dosage) {
    return FIELD_MESSAGES.dosageRequired
  }
  if (dosage.length > 100) {
    return FIELD_MESSAGES.dosageTooLong
  }
  return null
}

export function getExerciseTitleError(value: string): string | null {
  const title = value.trim()
  if (!title) {
    return FIELD_MESSAGES.titleRequired
  }
  if (title.length > 200) {
    return FIELD_MESSAGES.titleTooLong
  }
  return null
}
