/**
 * @file useSilentPoll.ts
 * @description Hook React realizujący ciche, okresowe odświeżanie danych w tle (cichy polling) w czasie, gdy dany ekran posiada aktywny fokus (z wykorzystaniem useFocusEffect).
 */

import { useCallback } from 'react'
import { useFocusEffect } from 'expo-router'

/**
 * Wykonuje cykliczne, ciche odświeżanie danych na aktywnym ekranie (używane m.in. na Androidzie jako uzupełnienie strumieniowania SSE).
 *
 * @param onTick - Funkcja wywoływana przy każdym takcie timera.
 * @param intervalMs - Interwał w milisekundach (domyślnie 7000 ms = 7 sekund).
 */
export function useSilentPoll(onTick: () => void, intervalMs = 7000): void {
  useFocusEffect(
    useCallback(() => {
      const id = setInterval(() => {
        onTick()
      }, intervalMs)
      return () => clearInterval(id)
    }, [onTick, intervalMs]),
  )
}
