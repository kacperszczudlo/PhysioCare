/**
 * @file types.ts
 * @description Definicje typów, stałych oraz funkcji pomocniczych klasyfikujących zdarzenia w czasie rzeczywistym (Realtime / SSE).
 */

/** Lista zdarzeń czasu rzeczywistego powiązanych z wizytami */
export const VISIT_REALTIME_TYPES = [
  'visit.scheduled',
  'visit.rescheduled',
  'visit.cancelled',
  'visit.approved',
  'visit.rejected',
] as const

/** Typ zdarzenia powiązanego z wizytą */
export type VisitRealtimeType = (typeof VISIT_REALTIME_TYPES)[number]

/** Pełna lista wszystkich obsługiwanych typów zdarzeń w czasie rzeczywistym */
export const REALTIME_EVENT_TYPES = [
  ...VISIT_REALTIME_TYPES,
  'document.created',
  'exercise.assigned',
  'ping',
] as const

/** Typ dowolnego zdarzenia w czasie rzeczywistym */
export type RealtimeEventType = (typeof REALTIME_EVENT_TYPES)[number]

/** Struktura obiektu zdarzenia odebranego przez SSE lub wysłanego do busa */
export interface RealtimeEvent {
  /** Typ zdarzenia */
  type: string
  /** Opcjonalny identyfikator powiązanego zasobu (np. ID wizyty) */
  resource_id: string | null
  /** Znacznik czasu wystąpienia zdarzenia w formacie ISO */
  at: string
}

/** Sprawdza, czy zdarzenie dotyczy wizyty pacjenta */
export function isVisitRealtimeEvent(event: RealtimeEvent): boolean {
  return (VISIT_REALTIME_TYPES as readonly string[]).includes(event.type)
}

/** Sprawdza, czy zdarzenie dotyczy nowego dokumentu medycznego */
export function isDocumentRealtimeEvent(event: RealtimeEvent): boolean {
  return event.type === 'document.created'
}

/** Sprawdza, czy zdarzenie dotyczy nowego przypisanego ćwiczenia */
export function isExerciseRealtimeEvent(event: RealtimeEvent): boolean {
  return event.type === 'exercise.assigned'
}

/** Sprawdza, czy zdarzenie wpływa na pulpit pacjenta (wizyty lub ćwiczenia) */
export function isDashboardRealtimeEvent(event: RealtimeEvent): boolean {
  return isVisitRealtimeEvent(event) || isExerciseRealtimeEvent(event)
}
