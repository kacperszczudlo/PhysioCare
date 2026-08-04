const DAY_START_HOUR = 7
const DAY_END_HOUR = 20
const SNAP_MINUTES = 15
export const PX_PER_MINUTE = 1.2

export function toDateInputValue(date: Date): string {
  const y = date.getFullYear()
  const m = String(date.getMonth() + 1).padStart(2, '0')
  const d = String(date.getDate()).padStart(2, '0')
  return `${y}-${m}-${d}`
}

export function parseDateInput(value: string): Date {
  const [y, m, d] = value.split('-').map(Number)
  return new Date(y, m - 1, d)
}

export function addDays(date: Date, days: number): Date {
  const next = new Date(date)
  next.setDate(next.getDate() + days)
  return next
}

export function startOfDay(date: Date): Date {
  return new Date(date.getFullYear(), date.getMonth(), date.getDate())
}

export function formatDayLabel(date: Date): string {
  return new Intl.DateTimeFormat('pl-PL', {
    weekday: 'long',
    day: 'numeric',
    month: 'long',
    year: 'numeric',
  }).format(date)
}

export function formatTime(date: Date): string {
  return new Intl.DateTimeFormat('pl-PL', {
    hour: '2-digit',
    minute: '2-digit',
  }).format(date)
}

export function dayBounds(date: Date): { start: Date; end: Date; minutes: number } {
  const start = new Date(date.getFullYear(), date.getMonth(), date.getDate(), DAY_START_HOUR, 0, 0, 0)
  const end = new Date(date.getFullYear(), date.getMonth(), date.getDate(), DAY_END_HOUR, 0, 0, 0)
  const minutes = (end.getTime() - start.getTime()) / 60_000
  return { start, end, minutes }
}

export function minutesFromDayStart(date: Date, day: Date): number {
  const { start } = dayBounds(day)
  return (date.getTime() - start.getTime()) / 60_000
}

export function snapMinutes(value: number): number {
  return Math.round(value / SNAP_MINUTES) * SNAP_MINUTES
}

export function clamp(value: number, min: number, max: number): number {
  return Math.min(max, Math.max(min, value))
}

export function dateFromDayMinutes(day: Date, minutes: number): Date {
  const { start } = dayBounds(day)
  return new Date(start.getTime() + minutes * 60_000)
}

export function hourMarks(day: Date): Date[] {
  const marks: Date[] = []
  for (let hour = DAY_START_HOUR; hour <= DAY_END_HOUR; hour += 1) {
    marks.push(new Date(day.getFullYear(), day.getMonth(), day.getDate(), hour, 0, 0, 0))
  }
  return marks
}

export function toIsoLocal(date: Date): string {
  const pad = (n: number) => String(n).padStart(2, '0')
  const offsetMin = -date.getTimezoneOffset()
  const sign = offsetMin >= 0 ? '+' : '-'
  const abs = Math.abs(offsetMin)
  const oh = pad(Math.floor(abs / 60))
  const om = pad(abs % 60)
  return (
    `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}` +
    `T${pad(date.getHours())}:${pad(date.getMinutes())}:${pad(date.getSeconds())}` +
    `${sign}${oh}:${om}`
  )
}

export { DAY_START_HOUR, DAY_END_HOUR, SNAP_MINUTES }
