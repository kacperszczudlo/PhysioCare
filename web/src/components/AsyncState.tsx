import type { ReactNode } from 'react'

import { Button } from '@/components/ui/Button'
import './AsyncState.css'

/** Prop-sy dla komponentu sygnalizującego stan ładowania danych. */
interface LoadingBlockProps {
  /** Komunikat informacyjny wyświetlany użytkownikowi (np. "Ładowanie listy pacjentów..."). */
  label?: string
  /** Wariant wizualny: dyskretna etykieta tekstowa ('text') lub pełny panel ('panel'). */
  variant?: 'text' | 'panel'
  /** Opcjonalny komponent szkieletowy (Skeleton) renderowany zamiast domyślnego wskaźnika. */
  skeleton?: ReactNode
}

/**
 * Komponent sygnalizujący pobieranie danych w toku (z dostępnością dla czytników ekranu WCAG).
 *
 * @example
 * <LoadingBlock label="Pobieranie historii wizyt..." variant="panel" />
 */
export function LoadingBlock({
  label = 'Ładowanie…',
  variant = 'text',
  skeleton,
}: LoadingBlockProps) {
  if (skeleton) {
    return (
      <div role="status" aria-busy="true" aria-live="polite" aria-label={label}>
        {skeleton}
      </div>
    )
  }
  return (
    <div
      className={variant === 'panel' ? 'async-loading async-loading--panel' : 'async-loading'}
      role="status"
      aria-busy="true"
      aria-live="polite"
    >
      <span className="async-loading__pulse" aria-hidden="true" />
      <p>{label}</p>
    </div>
  )
}

/** Prop-sy dla bannera prezentującego błąd pobierania lub operacji. */
interface ErrorBannerProps {
  /** Komunikat błędu do wyświetlenia w alertach UI. */
  message: string
  /** Opcjonalny callback umożliwiający użytkownikowi powtórzenie nieudanej operacji. */
  onRetry?: () => void
}

/**
 * Komponent bannera błędu z przyciskiem ponowienia akcji (`onRetry`).
 *
 * @example
 * <ErrorBanner message="Nie udało się pobrać danych pacjenta." onRetry={refetch} />
 */
export function ErrorBanner({ message, onRetry }: ErrorBannerProps) {
  return (
    <div className="async-error" role="alert">
      <p>{message}</p>
      {onRetry ? (
        <Button type="button" variant="secondary" size="sm" onClick={onRetry}>
          Spróbuj ponownie
        </Button>
      ) : null}
    </div>
  )
}

/** Prop-sy dla bannera potwierdzającego pomyślną operację. */
interface SuccessBannerProps {
  /** Treść komunikatu sukcesu (tekst lub JSX). */
  message: ReactNode
}

/**
 * Komponent bannera potwierdzającego pomyślny zapis lub zmianę stanu.
 */
export function SuccessBanner({ message }: SuccessBannerProps) {
  return (
    <div className="async-success" role="status" aria-live="polite">
      <p>{message}</p>
    </div>
  )
}

interface EmptyStateProps {
  title: string
  description?: string
  action?: ReactNode
}

export function EmptyState({ title, description, action }: EmptyStateProps) {
  return (
    <div className="async-empty" role="status">
      <p className="async-empty__title">{title}</p>
      {description ? <p className="async-empty__desc">{description}</p> : null}
      {action ? <div className="async-empty__action">{action}</div> : null}
    </div>
  )
}
