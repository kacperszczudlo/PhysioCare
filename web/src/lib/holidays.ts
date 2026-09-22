/**
 * Wylicza datę Niedzieli Wielkanocnej dla podanego roku przy użyciu algorytmu Meeusa/Jonesa/Butchera.
 *
 * @param year - Rok kalendarzowy.
 * @returns Obiekt Date reprezentujący Niedzielę Wielkanocną.
 */
export function getEasterDate(year: number): Date {
  const a = year % 19
  const b = Math.floor(year / 100)
  const c = year % 100
  const d = Math.floor(b / 4)
  const e = b % 4
  const f = Math.floor((b + 8) / 25)
  const g = Math.floor((b - f + 1) / 3)
  const h = (19 * a + b - d - g + 15) % 30
  const i = Math.floor(c / 4)
  const k = (c % 100) % 4
  const l = (32 + 2 * e + 2 * i - h - k) % 7
  const m = Math.floor((a + 11 * h + 22 * l) / 451)
  const month = Math.floor((h + l - 7 * m + 114) / 31)
  const day = ((h + l - 7 * m + 114) % 31) + 1
  return new Date(year, month - 1, day)
}

/**
 * Zwraca polską nazwę święta państwowego lub kościelnego ustawowo wolnego od pracy dla danej daty.
 *
 * @param date - Sprawdzana data.
 * @returns Nazwę święta (np. "Święto Pracy", "Boże Ciało") lub null, jeśli dzień jest zwykłym dniem roboczym.
 */
export function getPolishHolidayName(date: Date): string | null {
  const year = date.getFullYear()
  const month = date.getMonth() + 1
  const day = date.getDate()

  // Stałe święta ustawowe
  if (month === 1 && day === 1) return 'Nowy Rok'
  if (month === 1 && day === 6) return 'Trzech Króli'
  if (month === 5 && day === 1) return 'Święto Pracy'
  if (month === 5 && day === 3) return '3 Maja'
  if (month === 8 && day === 15) return 'Wniebowzięcie NMP'
  if (month === 11 && day === 1) return 'Wszystkich Świętych'
  if (month === 11 && day === 11) return 'Niepodległości'
  if (month === 12 && day === 25) return 'Boże Narodzenie'
  if (month === 12 && day === 26) return 'Boże Narodzenie'

  // Święta ruchome na podstawie Wielkanocy
  const easter = getEasterDate(year)
  const easterMs = easter.getTime()
  const targetMs = new Date(year, month - 1, day).getTime()
  const diffDays = Math.round((targetMs - easterMs) / (1000 * 60 * 60 * 24))

  if (diffDays === 0) return 'Wielkanoc'
  if (diffDays === 1) return 'Pon. Wielkanocny'
  if (diffDays === 49) return 'Zielone Świątki'
  if (diffDays === 60) return 'Boże Ciało'

  return null
}
