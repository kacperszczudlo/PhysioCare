/**
 * @file format.ts
 * @description Moduł funkcji pomocniczych do formatowania dat, godzin, zakresów czasowych oraz mapowania kluczy statusów na polskie etykiety.
 */

/**
 * Formatuje pełną datę i godzinę w formacie polskim (np. "wt., 22 wrz, 14:30").
 *
 * @param iso - Data i czas w formacie ISO-8601.
 * @returns Sformatowana data.
 */
export function formatDateTime(iso: string): string {
  const date = new Date(iso)
  if (Number.isNaN(date.getTime())) {
    return iso
  }
  return new Intl.DateTimeFormat('pl-PL', {
    weekday: 'short',
    day: 'numeric',
    month: 'short',
    hour: '2-digit',
    minute: '2-digit',
  }).format(date)
}

/**
 * Formatuje samą datę w języku polskim (np. "22 września 2026").
 *
 * @param iso - Data w formacie ISO-8601.
 * @returns Sformatowana data.
 */
export function formatDate(iso: string): string {
  const date = new Date(iso)
  if (Number.isNaN(date.getTime())) {
    return iso
  }
  return new Intl.DateTimeFormat('pl-PL', {
    day: 'numeric',
    month: 'long',
    year: 'numeric',
  }).format(date)
}

/**
 * Formatuje przedział godzinowy wizyty (np. "14:00-14:45").
 *
 * @param startIso - Czas rozpoczęcia w formacie ISO.
 * @param endIso - Czas zakończenia w formacie ISO.
 * @returns Sformatowany zakres godzin.
 */
export function formatTimeRange(startIso: string, endIso: string): string {
  const start = new Date(startIso)
  const end = new Date(endIso)
  if (Number.isNaN(start.getTime()) || Number.isNaN(end.getTime())) {
    return ''
  }
  const fmt = new Intl.DateTimeFormat('pl-PL', {
    hour: '2-digit',
    minute: '2-digit',
  })
  return `${fmt.format(start)}-${fmt.format(end)}`
}

/**
 * Zwraca dzisiejszą datę w formacie RRRR-MM-DD.
 *
 * @returns Ciąg znaków daty (np. "2026-09-22").
 */
export function todayISODate(): string {
  const now = new Date()
  const y = now.getFullYear()
  const m = String(now.getMonth() + 1).padStart(2, '0')
  const d = String(now.getDate()).padStart(2, '0')
  return `${y}-${m}-${d}`
}

/**
 * Dodaje określoną liczbę minut do podanego czasu ISO.
 *
 * @param iso - Czas początkowy w formacie ISO.
 * @param minutes - Liczba minut do dodania.
 * @returns Nowy czas w formacie ISO.
 */
export function addMinutesISO(iso: string, minutes: number): string {
  const date = new Date(iso)
  date.setMinutes(date.getMinutes() + minutes)
  return date.toISOString()
}

/**
 * Zwraca polską czytelną etykietę dla statusu wizyty.
 *
 * @param status - Kod statusu wizyty (np. 'SCHEDULED').
 * @returns Nazwa statusu po polsku.
 */
export function visitStatusLabel(status: string): string {
  switch (status) {
    case 'PENDING_APPROVAL':
      return 'Oczekuje na zatwierdzenie'
    case 'SCHEDULED':
      return 'Zaplanowana'
    case 'COMPLETED':
      return 'Zakończona'
    case 'CANCELLED':
      return 'Odwołana'
    case 'NO_SHOW':
      return 'Nieobecność'
    default:
      return status
  }
}

/**
 * Zwraca polską czytelną etykietę dla typu zgody prawnej.
 *
 * @param type - Kod zgody (np. 'TERMS_REQUIRED').
 * @returns Nazwa zgody po polsku.
 */
export function consentLabel(type: string): string {
  switch (type) {
    case 'TERMS_REQUIRED':
      return 'Regulamin'
    case 'MEDICAL_DATA_REQUIRED':
      return 'Dane medyczne'
    case 'MARKETING_OPTIONAL':
      return 'Marketing'
    case 'RESEARCH_OPTIONAL':
      return 'Badania naukowe'
    default:
      return type
  }
}

/**
 * Sprawdza, czy podany kod zgody jest zgodą obowiazkową do korzystania z systemu.
 *
 * @param type - Kod zgody.
 * @returns True jeśli zgoda jest wymagana.
 */
export function isRequiredConsent(type: string): boolean {
  return type === 'TERMS_REQUIRED' || type === 'MEDICAL_DATA_REQUIRED'
}

/** Słownik domyślnych etykiet dla preferencji powiadomień Push */
export const DEFAULT_NOTIFICATION_PREFS: Record<string, string> = {
  visit_reminder: 'Przypomnienia o wizytach',
  visit_change: 'Zmiany terminów',
  waitlist: 'Lista rezerwowa',
  exercise_reminder: 'Przypomnienia o ćwiczeniach',
  new_document: 'Nowe dokumenty',
}
