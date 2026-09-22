/**
 * @file bus.ts
 * @description Lokalna magistrala zdarzeń (Event Bus) do rozgłaszania powiadomień i aktualizacji w czasie rzeczywistym wewnątrz aplikacji.
 */

import type { RealtimeEvent } from './types'

/** Typ funkcji nasłuchującej na zdarzenia w czasie rzeczywistym */
type Listener = (event: RealtimeEvent) => void

/** Klasa reprezentująca magistralę zdarzeń wewnętrznych */
class RealtimeBus {
  private readonly listeners = new Set<Listener>()

  /**
   * Subskrybuje odbiorcę na przychodzące zdarzenia w czasie rzeczywistym.
   *
   * @param listener - Funkcja wywoływana przy nadejściu zdarzenia.
   * @returns Funkcja odsubskrybowująca odbiorcę.
   */
  subscribe(listener: Listener): () => void {
    this.listeners.add(listener)
    return () => {
      this.listeners.delete(listener)
    }
  }

  /**
   * Rozgłasza nowe zdarzenie do wszystkich zarejestrowanych odbiorców.
   *
   * @param event - Obiekt zdarzenia w czasie rzeczywistym.
   */
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

/** Instancja magistrali zdarzeń czasu rzeczywistego w aplikacji */
export const realtimeBus = new RealtimeBus()

