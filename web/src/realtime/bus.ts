import type { RealtimeEvent } from './types'

type Listener = (event: RealtimeEvent) => void

/**
 * Szyna zdarzeń czasu rzeczywistego (Pub/Sub Event Bus) obsługująca komunikację SSE wewnątrz aplikacji frontendowej.
 */
class RealtimeBus {
  private readonly listeners = new Set<Listener>()

  subscribe(listener: Listener): () => void {
    this.listeners.add(listener)
    return () => {
      this.listeners.delete(listener)
    }
  }

  emit(event: RealtimeEvent): void {
    for (const listener of this.listeners) {
      try {
        listener(event)
      } catch (error) {
        console.error('Realtime listener failed', error)
      }
    }
  }
}

export const realtimeBus = new RealtimeBus()
