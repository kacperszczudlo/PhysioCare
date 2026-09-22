/**
 * @file useRealtimeEvents.ts
 * @description Hook React służący do subskrybowania zdarzeń w czasie rzeczywistym z magistrali zdarzeń `realtimeBus`.
 */

import { useEffect } from 'react'

import { realtimeBus } from './bus'
import type { RealtimeEvent } from './types'

/**
 * Hook subskrybujący komponent na przychodzące zdarzenia z magistrali w czasie rzeczywistym.
 *
 * @param onEvent - Funkcja wywoływana przy zarejestrowaniu dowolnego zdarzenia RealtimeEvent.
 */
export function useRealtimeEvents(onEvent: (event: RealtimeEvent) => void): void {
  useEffect(() => realtimeBus.subscribe(onEvent), [onEvent])
}

