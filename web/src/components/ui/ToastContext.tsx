import { createContext, useCallback, useContext, useMemo, useState, type ReactNode } from 'react'

/** Wariant wizualny powiadomienia Toast (success, error, warning, info). */
export type ToastType = 'success' | 'error' | 'warning' | 'info'

/** Dodatkowa akcja w powiadomieniu (przycisk z etykietą i callbackiem). */
export interface ToastAction {
  label: string
  onClick: () => void
}

/** Opcje konfiguracji wyzwalania powiadomienia Toast. */
export interface ToastOptions {
  title?: string
  message: string
  type?: ToastType
  duration?: number
  action?: ToastAction
}

/** Wewnętrzne dane pojedynczego aktywnego powiadomienia w kolejce. */
export interface ToastItemData extends Required<Omit<ToastOptions, 'title' | 'action'>> {
  id: string
  title?: string
  action?: ToastAction
  createdAt: number
}

/** Zbiór właściwości i metod udostępnianych przez system powiadomień Toast. */
interface ToastContextValue {
  toasts: ToastItemData[]
  showToast: (options: ToastOptions | string, type?: ToastType) => string
  removeToast: (id: string) => void
  toast: {
    success: (message: string, options?: Omit<ToastOptions, 'message' | 'type'>) => string
    error: (message: string, options?: Omit<ToastOptions, 'message' | 'type'>) => string
    warning: (message: string, options?: Omit<ToastOptions, 'message' | 'type'>) => string
    info: (message: string, options?: Omit<ToastOptions, 'message' | 'type'>) => string
  }
}

const ToastContext = createContext<ToastContextValue | null>(null)

const DEFAULT_TOAST_DURATION = 4000

/**
 * Komponent dostawcy kontekstu powiadomień Toast w interfejsie użytkownika.
 */
export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<ToastItemData[]>([])

  const removeToast = useCallback((id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id))
  }, [])

  const showToast = useCallback(
    (options: ToastOptions | string, typeOverride?: ToastType): string => {
      const id = `toast-${Date.now()}-${Math.random().toString(36).substring(2, 9)}`

      let normalized: ToastOptions
      if (typeof options === 'string') {
        normalized = { message: options, type: typeOverride || 'info' }
      } else {
        normalized = { ...options, type: options.type || typeOverride || 'info' }
      }

      const newToast: ToastItemData = {
        id,
        title: normalized.title,
        message: normalized.message,
        type: normalized.type || 'info',
        duration: normalized.duration ?? DEFAULT_TOAST_DURATION,
        action: normalized.action,
        createdAt: Date.now(),
      }

      setToasts((prev) => [...prev.slice(-4), newToast])
      return id
    },
    [],
  )

  const toastHelpers = useMemo(
    () => ({
      success: (message: string, options?: Omit<ToastOptions, 'message' | 'type'>) =>
        showToast({ ...options, message, type: 'success' }),
      error: (message: string, options?: Omit<ToastOptions, 'message' | 'type'>) =>
        showToast({ ...options, message, type: 'error' }),
      warning: (message: string, options?: Omit<ToastOptions, 'message' | 'type'>) =>
        showToast({ ...options, message, type: 'warning' }),
      info: (message: string, options?: Omit<ToastOptions, 'message' | 'type'>) =>
        showToast({ ...options, message, type: 'info' }),
    }),
    [showToast],
  )

  const value = useMemo(
    () => ({
      toasts,
      showToast,
      removeToast,
      toast: toastHelpers,
    }),
    [toasts, showToast, removeToast, toastHelpers],
  )

  return <ToastContext.Provider value={value}>{children}</ToastContext.Provider>
}

/**
 * Hook React umożliwiający wyzwalanie powiadomień Toast (np. toast.success("Zapisano")).
 *
 * @returns Instancję ToastContextValue z metodami toast.success, toast.error, toast.warning, toast.info.
 *
 * @example
 * const { toast } = useToast();
 * toast.success("Poprawnie zaktualizowano dane pacjenta");
 */
// eslint-disable-next-line react-refresh/only-export-components
export function useToast(): ToastContextValue {
  const context = useContext(ToastContext)
  if (!context) {
    throw new Error('useToast must be used within a ToastProvider')
  }
  return context
}
