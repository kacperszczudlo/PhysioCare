import { useEffect } from 'react'

import { realtimeBus } from './bus'
import type { RealtimeEvent } from './types'

/**
 * Hook React subskrybujący zdarzenia w czasie rzeczywistym przychodzące ze magistrali SSE (realtimeBus).
 *
 * @param onEvent - Callback wywoływany przy odebraniu nowego powiadomienia (np. nowa rezerwacja wizyty).
 *
 * @example
 * useRealtimeEvents((event) => {
 *   if (event.type === 'VISIT_CREATED') refetchVisits();
 * });
 */
export function useRealtimeEvents(onEvent: (event: RealtimeEvent) => void): void {
  useEffect(() => realtimeBus.subscribe(onEvent), [onEvent])
}
