/**
 * @file offlineCache.ts
 * @description Pamięć podręczna dla odczytów danych pacjenta (pulpit, wizyty, ćwiczenia).
 * Umożliwia natychmiastowe wyświetlenie stanu aplikacji w trybie offline (Stale-While-Revalidate).
 */

import { tokenStorage } from '@/api/tokenStorage'
import type { ExercisePlanItem, TodayExercise, Visit } from '@/api/types'
import { getOfflineItem, setOfflineItem } from './offlineStorage'

const DASHBOARD_KEY = 'patient_dashboard_cache'
const VISITS_PREFIX = 'patient_visits_'
const EXERCISE_PREFIX = 'patient_exercise_'

async function getUserPrefix(): Promise<string> {
  try {
    const user = await tokenStorage.getCachedUser()
    if (user?.id) {
      return `u_${user.id}_`
    }
  } catch {}
  return 'u_anon_'
}

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
  const prefix = await getUserPrefix()
  const payload: CachedDashboardData = {
    ...data,
    updatedAt: new Date().toISOString(),
  }
  await setOfflineItem(`${prefix}${DASHBOARD_KEY}`, payload)
}

/**
 * Pobiera ostatni zapisany snapshot pulpitu pacjenta.
 */
export async function getCachedDashboard(): Promise<CachedDashboardData | null> {
  const prefix = await getUserPrefix()
  return getOfflineItem<CachedDashboardData>(`${prefix}${DASHBOARD_KEY}`)
}

/**
 * Zapisuje listę wizyt dla danej zakładki ('upcoming' | 'past' | 'all').
 */
export async function setCachedVisits(status: string, visits: Visit[]): Promise<void> {
  const prefix = await getUserPrefix()
  await setOfflineItem(`${prefix}${VISITS_PREFIX}${status}`, {
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
  const prefix = await getUserPrefix()
  return getOfflineItem<{ visits: Visit[]; updatedAt: string }>(
    `${prefix}${VISITS_PREFIX}${status}`,
  )
}

/**
 * Zapisuje szczegóły ćwiczenia w pamięci podręcznej.
 */
export async function setCachedExerciseDetail(
  id: number | string,
  item: TodayExercise | ExercisePlanItem,
): Promise<void> {
  const prefix = await getUserPrefix()
  await setOfflineItem(`${prefix}${EXERCISE_PREFIX}${id}`, {
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
  const prefix = await getUserPrefix()
  return getOfflineItem<{ item: TodayExercise | ExercisePlanItem; updatedAt: string }>(
    `${prefix}${EXERCISE_PREFIX}${id}`,
  )
}
