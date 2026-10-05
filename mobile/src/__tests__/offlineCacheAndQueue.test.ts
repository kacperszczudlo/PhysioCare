/**
 * @file offlineCacheAndQueue.test.ts
 * @description Testy jednostkowe pamięci podręcznej offline oraz kolejki operacji (outbox).
 */

import { describe, it, expect, beforeEach, vi } from 'vitest'
import {
  clearAllOfflineData,
  getOfflineItem,
  setOfflineItem,
  removeOfflineItem,
} from '../offline/offlineStorage'
import {
  getCachedDashboard,
  setCachedDashboard,
  getCachedVisits,
  setCachedVisits,
} from '../offline/offlineCache'
import {
  enqueueExerciseToggle,
  getPendingToggles,
  flushOfflineQueue,
  clearOfflineQueue,
} from '../offline/offlineQueue'
import { patientApi } from '../api/patient'
import { NetworkError } from '../api/client'
import type { Visit, TodayExercise, ExercisePlanItem } from '../api/types'

vi.mock('react-native', () => ({
  Platform: { OS: 'web' },
  TurboModuleRegistry: {
    getEnforcing: vi.fn(),
    get: vi.fn(),
  },
}))

vi.mock('expo-constants', () => ({
  default: {
    expoConfig: {
      extra: {},
    },
  },
}))

vi.mock('expo-secure-store', () => ({
  getItemAsync: vi.fn().mockResolvedValue(null),
  setItemAsync: vi.fn().mockResolvedValue(undefined),
  deleteItemAsync: vi.fn().mockResolvedValue(undefined),
}))

vi.mock('expo-file-system', () => ({
  documentDirectory: null,
  EncodingType: { UTF8: 'utf8' },
  getInfoAsync: vi.fn().mockResolvedValue({ exists: false }),
  makeDirectoryAsync: vi.fn().mockResolvedValue(undefined),
  writeAsStringAsync: vi.fn().mockResolvedValue(undefined),
  readAsStringAsync: vi.fn().mockResolvedValue(''),
  deleteAsync: vi.fn().mockResolvedValue(undefined),
}))

describe('offlineStorage & offlineCache', () => {
  beforeEach(async () => {
    await clearAllOfflineData()
  })

  it('zapisuje i odczytuje dowolny klucz w offlineStorage', async () => {
    await setOfflineItem('test_key', { foo: 'bar', num: 42 })
    const result = await getOfflineItem<{ foo: string; num: number }>('test_key')
    expect(result).toEqual({ foo: 'bar', num: 42 })

    await removeOfflineItem('test_key')
    const afterDelete = await getOfflineItem('test_key')
    expect(afterDelete).toBeNull()
  })

  it('keszuje i poprawnie zwraca snapshot pulpitu pacjenta', async () => {
    const mockVisits = [{ id: 'v1', status: 'SCHEDULED' }] as Visit[]
    const mockExercises = [
      { id: '10', exercise_title: 'Przysiady', completed_today: false },
    ] as unknown as TodayExercise[]
    const mockPlan = [] as ExercisePlanItem[]

    await setCachedDashboard({
      upcoming: mockVisits,
      past: [],
      todayExercises: mockExercises,
      activePlan: mockPlan,
    })

    const cached = await getCachedDashboard()
    expect(cached).not.toBeNull()
    expect(cached?.upcoming).toHaveLength(1)
    expect(cached?.upcoming[0].id).toBe('v1')
    expect(cached?.todayExercises[0].exercise_title).toBe('Przysiady')
    expect(cached?.updatedAt).toBeDefined()
  })

  it('keszuje i zwraca wizyty według statusu', async () => {
    const mockVisits = [{ id: 'v-up', status: 'SCHEDULED' }] as Visit[]
    await setCachedVisits('upcoming', mockVisits)

    const result = await getCachedVisits('upcoming')
    expect(result?.visits).toHaveLength(1)
    expect(result?.visits[0].id).toBe('v-up')
  })
})

describe('offlineQueue (Outbox)', () => {
  beforeEach(async () => {
    await clearAllOfflineData()
    await clearOfflineQueue()
    vi.restoreAllMocks()
  })

  it('dodaje operację do kolejki i aktualizuje duplikat dla tego samego dnia', async () => {
    await enqueueExerciseToggle(12, '2026-10-05', true)
    let queue = await getPendingToggles()
    expect(queue).toHaveLength(1)
    expect(queue[0].assignmentId).toBe(12)
    expect(queue[0].done).toBe(true)

    // Ponowne kliknięcie (zmiana na false) nie dubluje wpisu, lecz go nadpisuje
    await enqueueExerciseToggle(12, '2026-10-05', false)
    queue = await getPendingToggles()
    expect(queue).toHaveLength(1)
    expect(queue[0].done).toBe(false)
  })

  it('wysyła operacje z kolejki i opróżnia ją przy sukcesie API', async () => {
    vi.spyOn(patientApi, 'completeExercise').mockResolvedValue({
      id: 99,
      assignment: 15,
      completed_on: '2026-10-05',
      done: true,
      completed_at: new Date().toISOString(),
    } as any)

    await enqueueExerciseToggle(15, '2026-10-05', true)
    await enqueueExerciseToggle(16, '2026-10-05', true)

    const result = await flushOfflineQueue()
    expect(result.synced).toBe(2)
    expect(result.failed).toBe(0)

    const remaining = await getPendingToggles()
    expect(remaining).toHaveLength(0)
    expect(patientApi.completeExercise).toHaveBeenCalledTimes(2)
  })

  it('zachowuje operacje w kolejce w przypadku błędu sieci (NetworkError)', async () => {
    vi.spyOn(patientApi, 'completeExercise').mockRejectedValue(
      new NetworkError('offline', 'Brak połączenia z internetem'),
    )

    await enqueueExerciseToggle(20, '2026-10-05', true)

    const result = await flushOfflineQueue()
    expect(result.synced).toBe(0)
    expect(result.failed).toBe(1)

    // Wpis nadal czeka w kolejce na powrót sieci
    const remaining = await getPendingToggles()
    expect(remaining).toHaveLength(1)
    expect(remaining[0].assignmentId).toBe(20)
  })
})
