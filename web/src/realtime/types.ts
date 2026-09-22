/**
 * Typy zdarzeń czasu rzeczywistego powiązanych ze zmianami statusu wizyt fizjoterapeutycznych.
 */
export const VISIT_REALTIME_TYPES = [
  'visit.scheduled',
  'visit.rescheduled',
  'visit.cancelled',
  'visit.approved',
  'visit.rejected',
] as const

export type VisitRealtimeType = (typeof VISIT_REALTIME_TYPES)[number]

export const REALTIME_EVENT_TYPES = [
  ...VISIT_REALTIME_TYPES,
  'document.created',
  'exercise.assigned',
  'ping',
] as const

export type RealtimeEventType = (typeof REALTIME_EVENT_TYPES)[number]

export interface RealtimeEvent {
  type: string
  resource_id: string | null
  at: string
}

export function isVisitRealtimeEvent(event: RealtimeEvent): boolean {
  return (VISIT_REALTIME_TYPES as readonly string[]).includes(event.type)
}
