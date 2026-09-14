import type { ReactNode } from 'react'

import { Button } from '@/components/ui/Button'
import './AsyncState.css'

interface LoadingBlockProps {
  label?: string
  variant?: 'text' | 'panel'
  skeleton?: ReactNode
}

export function LoadingBlock({ label = 'Ładowanie…', variant = 'text', skeleton }: LoadingBlockProps) {
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

interface ErrorBannerProps {
  message: string
  onRetry?: () => void
}

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

interface SuccessBannerProps {
  message: ReactNode
}

export function SuccessBanner({ message }: SuccessBannerProps) {
  return (
    <div className="async-success" role="status">
      {typeof message === 'string' || typeof message === 'number' ? <p>{message}</p> : message}
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
