/**
 * @file DateTimePickerField.test.ts
 * @description Testy jednostkowe logiki przeliczania bębna przewijania oraz pomocników wyboru daty i godziny.
 */

import { describe, expect, it, vi } from 'vitest'

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

vi.mock('react-native', () => ({
  StyleSheet: { create: (s: any) => s },
  Text: 'Text',
  View: 'View',
  Pressable: 'Pressable',
  ScrollView: 'ScrollView',
}))

describe('DateTimePickerField Carousel Logic', () => {
  describe('indexFromOffset', () => {
    it('oblicza indeks 0 przy zerowym przesunięciu', () => {
      // Arrange & Act
      const index = indexFromOffset(0, 10, 44)

      // Assert
      expect(index).toBe(0)
    })

    it('oblicza poprawny indeks dla dodatniego przesunięcia w pionie', () => {
      // Arrange & Act & Assert
      expect(indexFromOffset(44, 10, 44)).toBe(1)
      expect(indexFromOffset(88, 10, 44)).toBe(2)
      expect(indexFromOffset(130, 10, 44)).toBe(3) // 130/44 = 2.95 -> zaokrąglenie do 3
    })

    it('ogranicza indeks do minimum (0) przy ujemnym skrollu', () => {
      // Arrange & Act
      const index = indexFromOffset(-20, 10, 44)

      // Assert
      expect(index).toBe(0)
    })

    it('ogranicza indeks do maksima (length - 1) po przewinięciu poza koniec', () => {
      // Arrange & Act
      const index = indexFromOffset(500, 10, 44)

      // Assert
      expect(index).toBe(9)
    })

    it('bezpiecznie obsługuje listę z jednym elementem', () => {
      // Arrange & Act
      const index = indexFromOffset(100, 1, 44)

      // Assert
      expect(index).toBe(0)
    })
  })

  describe('snapMinute', () => {
    it('zaokrągla minuty do najbliższego kroku', () => {
      // Arrange & Act & Assert
      expect(snapMinute(0, 15)).toBe(0)
      expect(snapMinute(7, 15)).toBe(0)
      expect(snapMinute(8, 15)).toBe(15)
      expect(snapMinute(22, 15)).toBe(15)
      expect(snapMinute(23, 15)).toBe(30)
    })

    it('zapobiega przekroczeniu 60 minut', () => {
      // Arrange & Act
      const snapped = snapMinute(58, 15)

      // Assert
      expect(snapped).toBe(45)
    })
  })

  describe('buildDays, buildHours, buildMinutes', () => {
    it('buduje dokładną liczbę dni poczynając od daty bazowej', () => {
      // Arrange
      const base = new Date('2026-09-15T10:00:00')

      // Act
      const days = buildDays(base, 7)

      // Assert
      expect(days).toHaveLength(7)
      expect(sameDay(days[0]!, base)).toBe(true)
      expect(days[6]?.getDate()).toBe(21)
    })

    it('poprawnie buduje zakres godzin pracy kliniki', () => {
      // Arrange & Act
      const hours = buildHours(7, 20)

      // Assert
      expect(hours).toHaveLength(14)
      expect(hours[0]).toBe(7)
      expect(hours[hours.length - 1]).toBe(20)
    })

    it('poprawnie buduje kroki minutowe', () => {
      // Arrange & Act
      const minutes = buildMinutes(15)

      // Assert
      expect(minutes).toEqual([0, 15, 30, 45])
    })
  })

  describe('clampDate and startOfDay', () => {
    it('normalizuje datę do początku dnia', () => {
      // Arrange
      const date = new Date('2026-09-15T15:45:12')

      // Act
      const start = startOfDay(date)

      // Assert
      expect(start.getHours()).toBe(0)
      expect(start.getMinutes()).toBe(0)
      expect(start.getSeconds()).toBe(0)
    })

    it('przycinają datę do minimalnej jeśli wejściowa jest wcześniejsza', () => {
      // Arrange
      const min = new Date('2026-09-20T00:00:00')
      const target = new Date('2026-09-15T00:00:00')

      // Act
      const clamped = clampDate(target, min)

      // Assert
      expect(clamped.getTime()).toBe(min.getTime())
    })
  })
})
