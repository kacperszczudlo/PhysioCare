/**
 * @file offlineQueue.ts
 * @description Kolejka operacji offline (Offline Outbox) pacjenta.
 * Przechowuje zaległe odhaczenia ćwiczeń wykonane w trybie offline i synchronizuje je
 * z serwerem API natychmiast po odzyskaniu połączenia z internetem.
 */

import { isNetworkFailure } from '@/api/client'
import { patientApi } from '@/api/patient'
import { getOfflineItem, setOfflineItem } from './offlineStorage'

const QUEUE_KEY = 'pending_exercise_toggles'

export interface QueuedExerciseToggle {
  id: string
  assignmentId: number | string
  completedOn?: string
  done: boolean
  timestamp: number
}

/**
 * Pobiera listę operacji oczekujących w kolejce offline.
 */
export async function getPendingToggles(): Promise<QueuedExerciseToggle[]> {
  const items = await getOfflineItem<QueuedExerciseToggle[]>(QUEUE_KEY)
  return Array.isArray(items) ? items : []
}

/**
 * Dodaje lub aktualizuje oczekujące odhaczenie ćwiczenia w kolejce offline.
 * W przypadku wielokrotnego kliknięcia dla tego samego ćwiczenia aktualizuje stan do najnowszego.
 */
export async function enqueueExerciseToggle(
  assignmentId: number | string,
  completedOn?: string,
  done = true,
): Promise<void> {
  const current = await getPendingToggles()
  const dateKey = completedOn ?? ''
  const existingIndex = current.findIndex(
    (item) => String(item.assignmentId) === String(assignmentId) && (item.completedOn ?? '') === dateKey,
  )

  const entry: QueuedExerciseToggle = {
    id: `${assignmentId}_${dateKey || 'today'}_${Date.now()}`,
    assignmentId,
    completedOn,
    done,
    timestamp: Date.now(),
  }

  let updated: QueuedExerciseToggle[]
  if (existingIndex >= 0) {
    updated = [...current]
    updated[existingIndex] = entry
  } else {
    updated = [...current, entry]
  }

  await setOfflineItem(QUEUE_KEY, updated)
}

/**
 * Usuwa z kolejki wpis o danym id.
 */
export async function removeQueueItem(id: string): Promise<void> {
  const current = await getPendingToggles()
  const next = current.filter((item) => item.id !== id)
  await setOfflineItem(QUEUE_KEY, next)
}

/**
 * Czyści całą kolejkę offline (np. przy wylogowaniu).
 */
export async function clearOfflineQueue(): Promise<void> {
  await setOfflineItem(QUEUE_KEY, [])
}

/**
 * Opróżnia kolejkę wysyłając zaległe operacje do backendu API.
 * W przypadku braku sieci przerywa działanie i zachowuje pozostałe wpisy na później.
 *
 * @returns Podsumowanie wykonanych i nieudanych synchronizacji.
 */
export async function flushOfflineQueue(): Promise<{ synced: number; failed: number }> {
  const current = await getPendingToggles()
  if (current.length === 0) {
    return { synced: 0, failed: 0 }
  }

  let synced = 0
  let failed = 0
  const remaining: QueuedExerciseToggle[] = []

  for (const item of current) {
    try {
      await patientApi.completeExercise(String(item.assignmentId), item.completedOn, item.done)
      synced++
    } catch (err) {
      if (isNetworkFailure(err)) {
        // Nadal brak sieci – zostawiamy ten i wszystkie kolejne w kolejce
        remaining.push(item)
        failed++
        // Przerwij pętlę, nie ma sensu ponawiać reszty w tym samym cyklu bez internetu
        const idx = current.indexOf(item)
        remaining.push(...current.slice(idx + 1))
        break
      } else {
        // Błąd biznesowy (np. usunięte zalecenie, 404 lub 400) – usuwamy, by nie blokowało kolejki
        console.warn('Permanent failure syncing offline exercise toggle', item, err)
        failed++
      }
    }
  }

  await setOfflineItem(QUEUE_KEY, remaining)
  return { synced, failed }
}
