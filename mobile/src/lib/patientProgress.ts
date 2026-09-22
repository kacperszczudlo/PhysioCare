/**
 * @file patientProgress.ts
 * @description Moduł obliczania statystyk i postępu pacjenta (zrealizowane ćwiczenia w ujęciu tygodniowym, zrealizowane oraz nadchodzące wizyty).
 */

import type { ExercisePlanItem, Visit } from '@/api/types'

/**
 * Postęp wykonywania ćwiczeń w konkretnym dniu kalendarzowym.
 */
export interface DayProgress {
  /** Data w formacie RRRR-MM-DD */
  date: string
  /** Krótka nazwa dnia tygodnia (np. "pn", "wt") */
  label: string
  /** Liczba wykonanych ćwiczeń w danym dniu */
  done: number
  /** Łączna liczba przypisanych ćwiczeń na ten dzień */
  total: number
  /** Współczynnik ukończenia od 0 do 1 (0 w przypadku braku ćwiczeń) */
  ratio: number
  /** Czy dany dzień jest dniem dzisiejszym */
  isToday: boolean
}

/** Zamienia obiekt Date na lokalny ciąg znaków RRRR-MM-DD */
function toLocalISODate(date: Date): string {
  const y = date.getFullYear()
  const m = String(date.getMonth() + 1).padStart(2, '0')
  const d = String(date.getDate()).padStart(2, '0')
  return `${y}-${m}-${d}`
}

/** Zwraca obiekt Date wyzerowany do godziny 00:00:00.000 */
function startOfLocalDay(date: Date): Date {
  return new Date(date.getFullYear(), date.getMonth(), date.getDate())
}

/** Parsuje ciąg daty RRRR-MM-DD na lokalny obiekt Date */
function parseISODateLocal(iso: string): Date {
  const [y, m, d] = iso.split('-').map(Number)
  return new Date(y, (m ?? 1) - 1, d ?? 1)
}

/**
 * Oblicza dzienny postęp wykonywania planu ćwiczeń dla ostatnich N dni (domyślnie 7).
 *
 * @param assignments - Lista przypisanych zadań treningowych.
 * @param days - Liczba dni wstecz do uwzględnienia (domyślnie 7).
 * @param now - Aktualna data referencyjna.
 * @returns Tablica obiektów `DayProgress` reprezentująca postęp dzień po dniu.
 */
export function buildWeekExerciseProgress(
  assignments: ExercisePlanItem[],
  days = 7,
  now = new Date(),
): DayProgress[] {
  const today = startOfLocalDay(now)
  const weekdayFmt = new Intl.DateTimeFormat('pl-PL', { weekday: 'short' })
  const result: DayProgress[] = []

  for (let offset = days - 1; offset >= 0; offset -= 1) {
    const day = new Date(today)
    day.setDate(today.getDate() - offset)
    const date = toLocalISODate(day)

    let total = 0
    let done = 0
    for (const item of assignments) {
      const start = parseISODateLocal(item.start_date)
      const end = parseISODateLocal(item.end_date)
      if (day < start || day > end) {
        continue
      }
      total += 1
      const completed = item.completions?.some((c) => c.done && c.completed_on === date)
      if (completed) {
        done += 1
      }
    }

    result.push({
      date,
      label: weekdayFmt.format(day).replace('.', ''),
      done,
      total,
      ratio: total > 0 ? done / total : 0,
      isToday: offset === 0,
    })
  }

  return result
}

/**
 * Zlicza liczbę wizyt o statucie 'COMPLETED' (zakończone).
 *
 * @param visits - Lista wizyt pacjenta.
 * @returns Liczba zakończonych wizyt.
 */
export function countCompletedVisits(visits: Visit[]): number {
  return visits.filter((v) => v.status === 'COMPLETED').length
}

/**
 * Zlicza liczbę zaplanowanych lub oczekujących wizyt.
 *
 * @param visits - Lista wizyt pacjenta.
 * @returns Liczba nadchodzących wizyt.
 */
export function countUpcomingVisits(visits: Visit[]): number {
  return visits.filter((v) => v.status === 'SCHEDULED' || v.status === 'PENDING_APPROVAL').length
}
