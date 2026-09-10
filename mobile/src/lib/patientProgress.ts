import type { ExercisePlanItem, Visit } from '@/api/types'

export interface DayProgress {
  /** Local calendar date YYYY-MM-DD */
  date: string
  /** Short weekday label in pl-PL, e.g. "pn" */
  label: string
  done: number
  total: number
  /** 0–1 completion ratio; 0 when nothing was assigned that day */
  ratio: number
  isToday: boolean
}

function toLocalISODate(date: Date): string {
  const y = date.getFullYear()
  const m = String(date.getMonth() + 1).padStart(2, '0')
  const d = String(date.getDate()).padStart(2, '0')
  return `${y}-${m}-${d}`
}

function startOfLocalDay(date: Date): Date {
  return new Date(date.getFullYear(), date.getMonth(), date.getDate())
}

function parseISODateLocal(iso: string): Date {
  const [y, m, d] = iso.split('-').map(Number)
  return new Date(y, (m ?? 1) - 1, d ?? 1)
}

/** Last `days` calendar days inclusive, ending today. */
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
      const completed = item.completions?.some(
        (c) => c.done && c.completed_on === date,
      )
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

export function countCompletedVisits(visits: Visit[]): number {
  return visits.filter((v) => v.status === 'COMPLETED').length
}

export function countUpcomingVisits(visits: Visit[]): number {
  return visits.filter(
    (v) => v.status === 'SCHEDULED' || v.status === 'PENDING_APPROVAL',
  ).length
}
