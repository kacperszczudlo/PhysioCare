/**
 * @file patientProgress.test.ts
 * @description Testy jednostkowe przeliczania statystyk postępów pacjenta (zliczenie wizyt i postępu ćwiczeń w 7 dniach).
 */

import { describe, it, expect } from 'vitest'
import {
  buildWeekExerciseProgress,
  countCompletedVisits,
  countUpcomingVisits,
} from '../lib/patientProgress'
import type { Visit } from '../api/types'

describe('patientProgress (Mobile)', () => {
  it('dokładnie zlicza zakończone i nadchodzące wizyty', () => {
    // Arrange
    const visits = [
      { id: '1', status: 'COMPLETED' },
      { id: '2', status: 'SCHEDULED' },
      { id: '3', status: 'PENDING_APPROVAL' },
      { id: '4', status: 'CANCELLED' },
    ] as Visit[]

    // Act
    const completed = countCompletedVisits(visits)
    const upcoming = countUpcomingVisits(visits)

    // Assert
    expect(completed).toBe(1)
    expect(upcoming).toBe(2)
  })

  it('buduje wskaźnik wykonania ćwiczeń z 7 dni', () => {
    // Arrange
    const now = new Date('2026-09-14T10:00:00Z')
    const assignments = [
      {
        id: 'a1',
        start_date: '2026-09-10',
        end_date: '2026-09-20',
        completions: [{ done: true, completed_on: '2026-09-14' }],
      },
    ] as any

    // Act
    const progress = buildWeekExerciseProgress(assignments, 7, now)

    // Assert
    expect(progress).toHaveLength(7)
    const today = progress.find((p) => p.isToday)
    expect(today).toBeDefined()
    expect(today?.date).toBe('2026-09-14')
    expect(today?.done).toBe(1)
    expect(today?.ratio).toBe(1)
  })
})
