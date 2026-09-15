import { describe, expect, it, vi } from 'vitest'

vi.mock('react-native', () => ({
  StyleSheet: { create: (s: any) => s },
  Text: 'Text',
  View: 'View',
  Pressable: 'Pressable',
  ScrollView: 'ScrollView',
}))

import {
  buildDays,
  buildHours,
  buildMinutes,
  clampDate,
  indexFromOffset,
  sameDay,
  snapMinute,
  startOfDay,
} from '../components/DateTimePickerField'

describe('DateTimePickerField Carousel Logic', () => {
  describe('indexFromOffset', () => {
    it('calculates 0 index at top scroll offset', () => {
      expect(indexFromOffset(0, 10, 44)).toBe(0)
    })

    it('calculates correct index for positive scroll offset', () => {
      expect(indexFromOffset(44, 10, 44)).toBe(1)
      expect(indexFromOffset(88, 10, 44)).toBe(2)
      expect(indexFromOffset(130, 10, 44)).toBe(3) // 130/44 = 2.95 -> rounds to 3
    })

    it('clamps to min index (0) when scrolled negative', () => {
      expect(indexFromOffset(-20, 10, 44)).toBe(0)
    })

    it('clamps to max index (length - 1) when scrolled past end', () => {
      expect(indexFromOffset(500, 10, 44)).toBe(9)
    })

    it('handles single item list safely', () => {
      expect(indexFromOffset(100, 1, 44)).toBe(0)
    })
  })

  describe('snapMinute', () => {
    it('snaps minute to nearest step', () => {
      expect(snapMinute(0, 15)).toBe(0)
      expect(snapMinute(7, 15)).toBe(0)
      expect(snapMinute(8, 15)).toBe(15)
      expect(snapMinute(22, 15)).toBe(15)
      expect(snapMinute(23, 15)).toBe(30)
    })

    it('prevents overflow to 60 minutes', () => {
      expect(snapMinute(58, 15)).toBe(45)
    })
  })

  describe('buildDays, buildHours, buildMinutes', () => {
    it('builds exact count of days starting from base date', () => {
      const base = new Date('2026-09-15T10:00:00')
      const days = buildDays(base, 7)
      expect(days).toHaveLength(7)
      expect(sameDay(days[0]!, base)).toBe(true)
      expect(days[6]?.getDate()).toBe(21)
    })

    it('builds clinic hours range correctly', () => {
      const hours = buildHours(7, 20)
      expect(hours).toHaveLength(14)
      expect(hours[0]).toBe(7)
      expect(hours[hours.length - 1]).toBe(20)
    })

    it('builds minute steps correctly', () => {
      const minutes = buildMinutes(15)
      expect(minutes).toEqual([0, 15, 30, 45])
    })
  })

  describe('clampDate and startOfDay', () => {
    it('normalizes date to start of day', () => {
      const date = new Date('2026-09-15T15:45:12')
      const start = startOfDay(date)
      expect(start.getHours()).toBe(0)
      expect(start.getMinutes()).toBe(0)
      expect(start.getSeconds()).toBe(0)
    })

    it('clamps date to minimum date if earlier than min', () => {
      const min = new Date('2026-09-20T00:00:00')
      const target = new Date('2026-09-15T00:00:00')
      expect(clampDate(target, min).getTime()).toBe(min.getTime())
    })
  })
})
