import { describe, it, expect } from 'vitest'
import {
  toDateInputValue,
  parseDateInput,
  addDays,
  snapMinutes,
  clamp,
  dayBounds,
} from '../lib/scheduleTime'

describe('scheduleTime (Web)', () => {
  it('converts date to YYYY-MM-DD input string and back', () => {
    const date = new Date(2026, 8, 14) // Sep 14, 2026
    const str = toDateInputValue(date)
    expect(str).toBe('2026-09-14')

    const parsed = parseDateInput(str)
    expect(parsed.getFullYear()).toBe(2026)
    expect(parsed.getMonth()).toBe(8)
    expect(parsed.getDate()).toBe(14)
  })

  it('adds days correctly', () => {
    const date = new Date(2026, 8, 14)
    const next = addDays(date, 5)
    expect(next.getDate()).toBe(19)
  })

  it('snaps minutes to 15-minute intervals', () => {
    expect(snapMinutes(7)).toBe(0)
    expect(snapMinutes(8)).toBe(15)
    expect(snapMinutes(23)).toBe(30)
  })

  it('clamps values within bounds', () => {
    expect(clamp(5, 0, 10)).toBe(5)
    expect(clamp(-5, 0, 10)).toBe(0)
    expect(clamp(15, 0, 10)).toBe(10)
  })

  it('calculates day bounds from 07:00 to 20:00', () => {
    const bounds = dayBounds(new Date(2026, 8, 14))
    expect(bounds.start.getHours()).toBe(7)
    expect(bounds.end.getHours()).toBe(20)
    expect(bounds.minutes).toBe(13 * 60) // 780 minutes
  })
})
