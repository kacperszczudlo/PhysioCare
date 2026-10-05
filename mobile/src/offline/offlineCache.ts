/**
 * @file offlineCache.ts
 * @description Pamięć podręczna dla odczytów danych pacjenta (pulpit, wizyty, ćwiczenia).
 * Umożliwia natychmiastowe wyświetlenie stanu aplikacji w trybie offline (Stale-While-Revalidate).
 */

import type { ExercisePlanItem, TodayExercise, Visit } from '@/api/types'
import { getOfflineItem, setOfflineItem } from './offlineStorage'

const DASHBOARD_KEY = 'patient_dashboard_cache'
const VISITS_PREFIX = 'patient_visits_'
const EXERCISE_PREFIX = 'patient_exercise_'

export interface CachedDashboardData {
  upcoming: Visit[]
  past: Visit[]
  todayExercises: TodayExercise[]
  activePlan: ExercisePlanItem[]
  updatedAt: string
}

/**
 * Zapisuje snapshot pulpitu pacjenta w pamięci offline.
 */
export async function setCachedDashboard(data: {
  upcoming: Visit[]
  past: Visit[]
  todayExercises: TodayExercise[]
  activePlan: ExercisePlanItem[]
}): Promise<void> {
  const payload: CachedDashboardData = {
    ...data,
    updatedAt: new Date().toISOString(),
  }
  await setOfflineItem(DASHBOARD_KEY, payload)
}

/**
 * Pobiera ostatni zapisany snapshot pulpitu pacjenta.
 */
export async function getCachedDashboard(): Promise<CachedDashboardData | null> {
  return getOfflineItem<CachedDashboardData>(DASHBOARD_KEY)
}

/**
 * Zapisuje listę wizyt dla danej zakładki ('upcoming' | 'past' | 'all').
 */
export async function setCachedVisits(status: string, visits: Visit[]): Promise<void> {
  await setOfflineItem(`${VISITS_PREFIX}${status}`, {
    visits,
    updatedAt: new Date().toISOString(),
  })
}

/**
 * Pobiera zapisaną listę wizyt dla danej zakładki.
 */
export async function getCachedVisits(
  status: string,
): Promise<{ visits: Visit[]; updatedAt: string } | null> {
  return getOfflineItem<{ visits: Visit[]; updatedAt: string }>(`${VISITS_PREFIX}${status}`)
}

/**
 * Zapisuje szczegóły ćwiczenia w pamięci podręcznej.
 */
export async function setCachedExerciseDetail(
  id: number | string,
  item: TodayExercise | ExercisePlanItem,
): Promise<void> {
  await setOfflineItem(`${EXERCISE_PREFIX}${id}`, {
    item,
    updatedAt: new Date().toISOString(),
  })
}

/**
 * Pobiera zapamiętane szczegóły konkretnego ćwiczenia.
 */
export async function getCachedExerciseDetail(
  id: number | string,
): Promise<{ item: TodayExercise | ExercisePlanItem; updatedAt: string } | null> {
  return getOfflineItem<{ item: TodayExercise | ExercisePlanItem; updatedAt: string }>(
    `${EXERCISE_PREFIX}${id}`,
  )
}
