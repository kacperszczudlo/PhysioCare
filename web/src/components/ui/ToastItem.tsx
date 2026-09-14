import { useCallback, useEffect, useRef, useState } from 'react'
import type { ToastItemData } from './ToastContext'

interface ToastItemProps {
  toast: ToastItemData
  onClose: (id: string) => void
}

function StatusIcon({ type }: { type: ToastItemData['type'] }) {
  switch (type) {
    case 'success':
      return (
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
          <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
          <polyline points="22 4 12 14.01 9 11.01" />
        </svg>
      )
    case 'error':
      return (
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
          <circle cx="12" cy="12" r="10" />
          <line x1="15" y1="9" x2="9" y2="15" />
          <line x1="9" y1="9" x2="15" y2="15" />
        </svg>
      )
    case 'warning':
      return (
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
          <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
          <line x1="12" y1="9" x2="12" y2="13" />
          <line x1="12" y1="17" x2="12.01" y2="17" />
        </svg>
      )
    case 'info':
    default:
      return (
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
          <circle cx="12" cy="12" r="10" />
          <line x1="12" y1="16" x2="12" y2="12" />
          <line x1="12" y1="8" x2="12.01" y2="8" />
        </svg>
      )
  }
}

export function ToastItem({ toast, onClose }: ToastItemProps) {
  const [isExiting, setIsExiting] = useState(false)
  const [progress, setProgress] = useState(100)
  const [isPaused, setIsPaused] = useState(false)

  const remainingTimeRef = useRef(toast.duration)
  const lastTickRef = useRef<number | null>(null)
  const animationFrameRef = useRef<number | null>(null)

  const handleDismiss = useCallback(() => {
    setIsExiting(true)
    setTimeout(() => onClose(toast.id), 200)
  }, [onClose, toast.id])

  useEffect(() => {
    if (toast.duration <= 0) return

    lastTickRef.current = performance.now()

    const updateTimer = (now: number) => {
      if (!isPaused && lastTickRef.current !== null) {
        const delta = now - lastTickRef.current
        remainingTimeRef.current -= delta

        if (remainingTimeRef.current <= 0) {
          setProgress(0)
          handleDismiss()
          return
        }

        setProgress(Math.max(0, (remainingTimeRef.current / toast.duration) * 100))
      }
      lastTickRef.current = now
      animationFrameRef.current = requestAnimationFrame(updateTimer)
    }

    animationFrameRef.current = requestAnimationFrame(updateTimer)

    return () => {
      if (animationFrameRef.current !== null) {
        cancelAnimationFrame(animationFrameRef.current)
      }
    }
  }, [toast.duration, isPaused, handleDismiss])

  const ariaRole = toast.type === 'error' ? 'alert' : 'status'

  return (
    <div
      className={`toast-item toast-item--${toast.type} ${isExiting ? 'toast-item--exiting' : ''}`}
      role={ariaRole}
      aria-live={toast.type === 'error' ? 'assertive' : 'polite'}
      onMouseEnter={() => setIsPaused(true)}
      onMouseLeave={() => setIsPaused(false)}
    >
      <div className="toast-item__icon">
        <StatusIcon type={toast.type} />
      </div>

      <div className="toast-item__content">
        {toast.title && <div className="toast-item__title">{toast.title}</div>}
        <div className="toast-item__message">{toast.message}</div>
        {toast.action && (
          <button
            type="button"
            className="toast-item__action"
            onClick={() => {
              toast.action?.onClick()
              handleDismiss()
            }}
          >
            {toast.action.label}
          </button>
        )}
      </div>

      <button
        type="button"
        className="toast-item__close"
        onClick={handleDismiss}
        aria-label="Zamknij powiadomienie"
      >
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <line x1="18" y1="6" x2="6" y2="18" />
          <line x1="6" y1="6" x2="18" y2="18" />
        </svg>
      </button>

      {toast.duration > 0 && (
        <div
          className="toast-item__progress"
          style={{ width: `${progress}%` }}
          aria-hidden="true"
        />
      )}
    </div>
  )
}
