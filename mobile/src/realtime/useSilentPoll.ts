import { useCallback } from 'react'
import { useFocusEffect } from 'expo-router'

/**
 * Soft refresh while the screen is focused.
 * Android often cannot stream infinite SSE via XHR - poll keeps UI live.
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
