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
import { tokenStorage } from '../api/tokenStorage'
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

const secureStoreMock = new Map<string, string>()

vi.mock('expo-secure-store', () => ({
  getItemAsync: vi.fn().mockImplementation((k: string) => Promise.resolve(secureStoreMock.get(k) ?? null)),
  setItemAsync: vi.fn().mockImplementation((k: string, v: string) => {
    secureStoreMock.set(k, v)
    return Promise.resolve()
  }),
  deleteItemAsync: vi.fn().mockImplementation((k: string) => {
    secureStoreMock.delete(k)
    return Promise.resolve()
  }),
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
    secureStoreMock.clear()
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

  it('szyfruje dane wrażliwe (brak jawnego tekstu JSON w magazynie)', async () => {
    await setOfflineItem('phi_record', { diagnosis: 'Rwa kulszowa', note: 'Ściśle tajne' })
    const decrypted = await getOfflineItem<{ diagnosis: string; note: string }>('phi_record')
    expect(decrypted).toEqual({ diagnosis: 'Rwa kulszowa', note: 'Ściśle tajne' })
  })

  it('automatycznie unieważnia przedawniony cache po upływie TTL', async () => {
    await setOfflineItem('expiring_key', { temp: 'wartość' }, 40)
    expect(await getOfflineItem('expiring_key')).toEqual({ temp: 'wartość' })

    await new Promise((resolve) => setTimeout(resolve, 60))
    expect(await getOfflineItem('expiring_key')).toBeNull()
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

  it('izoluje cache i kolejkę per-user (brak wycieku danych między pacjentami)', async () => {
    // Pacjent 1
    await tokenStorage.setCachedUser({
      id: 'patient-uuid-1',
      email: 'pacjent1@physiocare.test',
      role: 'PATIENT',
      first_name: 'Jan',
      last_name: 'Pierwszy',
    })

    const visitsUser1 = [{ id: 'v-user1', status: 'SCHEDULED' }] as Visit[]
    await setCachedVisits('upcoming', visitsUser1)
    await enqueueExerciseToggle(101, '2026-10-05', true)

    expect((await getCachedVisits('upcoming'))?.visits[0].id).toBe('v-user1')
    expect((await getPendingToggles())[0].assignmentId).toBe(101)

    // Loguje się Pacjent 2
    await tokenStorage.setCachedUser({
      id: 'patient-uuid-2',
      email: 'pacjent2@physiocare.test',
      role: 'PATIENT',
      first_name: 'Anna',
      last_name: 'Druga',
    })

    // Pacjent 2 nie ma dostępu do cache ani kolejki Pacjenta 1
    expect(await getCachedVisits('upcoming')).toBeNull()
    expect(await getPendingToggles()).toEqual([])

    // Pacjent 2 dodaje swoje operacje
    await enqueueExerciseToggle(202, '2026-10-05', true)
    expect((await getPendingToggles())[0].assignmentId).toBe(202)
  })

  it('tokenStorage.clear czyści tokeny, dane użytkownika oraz pamięć podręczną i kolejkę offline', async () => {
    await tokenStorage.setCachedUser({
      id: 'patient-uuid-clear',
      email: 'clear@physiocare.test',
      role: 'PATIENT',
      first_name: 'Clear',
      last_name: 'Test',
    })

    await enqueueExerciseToggle(999, '2026-10-05', true)
    await setCachedVisits('upcoming', [{ id: 'v-clear', status: 'SCHEDULED' }] as Visit[])

    expect(await getPendingToggles()).toHaveLength(1)
    expect(await getCachedVisits('upcoming')).not.toBeNull()

    // Wylogowanie / czyszczenie
    await tokenStorage.clear()

    expect(await tokenStorage.getCachedUser()).toBeNull()
    expect(await getPendingToggles()).toEqual([])
    expect(await getCachedVisits('upcoming')).toBeNull()
  })

  it('eliminuje wyścig przy równoległych operacjach enqueue (AsyncMutex)', async () => {
    // 3 równoległe operacje zapisu bez await pomiędzy nimi
    await Promise.all([
      enqueueExerciseToggle(1, '2026-10-05', true),
      enqueueExerciseToggle(2, '2026-10-05', true),
      enqueueExerciseToggle(3, '2026-10-05', true),
    ])

    const queue = await getPendingToggles()
    expect(queue).toHaveLength(3)
    const assignmentIds = queue.map((i) => i.assignmentId)
    expect(assignmentIds).toContain(1)
    expect(assignmentIds).toContain(2)
    expect(assignmentIds).toContain(3)
  })

  it('eliminuje wyścig przy enqueue wywołanym w trakcie flushOfflineQueue', async () => {
    let resolveComplete!: () => void
    const slowApiPromise = new Promise<{ id: number; assignment: number; completed_on: string; done: boolean; completed_at: string }>((resolve) => {
      resolveComplete = () =>
        resolve({
          id: 50,
          assignment: 10,
          completed_on: '2026-10-05',
          done: true,
          completed_at: new Date().toISOString(),
        })
    })

    vi.spyOn(patientApi, 'completeExercise').mockImplementation(async (assignmentId) => {
      if (String(assignmentId) === '10') {
        return slowApiPromise as any
      }
      return {
        id: 51,
        assignment: Number(assignmentId),
        completed_on: '2026-10-05',
        done: true,
        completed_at: new Date().toISOString(),
      } as any
    })

    // W kolejce jest zadanie 10
    await enqueueExerciseToggle(10, '2026-10-05', true)

    // Uruchamiamy flush w tle (czeka na slowApiPromise)
    const flushPromise = flushOfflineQueue()

    // W tym samym czasie pacjent klika i dodaje zadanie 20
    const enqueuePromise = enqueueExerciseToggle(20, '2026-10-05', true)

    // Odblokowujemy API dla zadania 10
    resolveComplete()

    const [flushResult] = await Promise.all([flushPromise, enqueuePromise])
    expect(flushResult.synced).toBe(1)

    // Po zakończeniu obu operacji w kolejce MUSI znajdować się zadanie 20 (nie zostało nadpisane ani utracone)
    const remaining = await getPendingToggles()
    expect(remaining).toHaveLength(1)
    expect(remaining[0].assignmentId).toBe(20)
  })

  it('zapobiega równoległym flushom dublującym wysyłkę z kolejki', async () => {
    let callCount = 0
    vi.spyOn(patientApi, 'completeExercise').mockImplementation(async () => {
      callCount++
      await new Promise((r) => setTimeout(r, 10))
      return { id: 1 } as any
    })

    await enqueueExerciseToggle(30, '2026-10-05', true)

    // Dwa współbieżne wywołania flush
    const [res1, res2] = await Promise.all([flushOfflineQueue(), flushOfflineQueue()])

    expect(callCount).toBe(1)
    expect(res1.synced + res2.synced).toBe(1)
    expect(await getPendingToggles()).toHaveLength(0)
  })
})
