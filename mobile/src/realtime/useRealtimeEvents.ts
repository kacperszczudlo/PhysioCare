import { useEffect } from 'react'

import { realtimeBus } from './bus'
import type { RealtimeEvent } from './types'

export function useRealtimeEvents(onEvent: (event: RealtimeEvent) => void): void {
  useEffect(() => realtimeBus.subscribe(onEvent), [onEvent])
}
