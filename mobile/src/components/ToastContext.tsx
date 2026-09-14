import React, {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState,
  type ReactNode,
} from 'react'
import { Vibration } from 'react-native'

export type ToastType = 'success' | 'error' | 'warning' | 'info'

export interface ToastAction {
  label: string
  onPress: () => void
}

export interface ToastOptions {
  title?: string
  message: string
  type?: ToastType
  duration?: number
  action?: ToastAction
}

export interface ToastItemData extends Required<Omit<ToastOptions, 'title' | 'action'>> {
  id: string
  title?: string
  action?: ToastAction
  createdAt: number
}

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

export const DEFAULT_TOAST_DURATION = 4000

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<ToastItemData[]>([])

  const removeToast = useCallback((id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id))
  }, [])

  const triggerHapticFeedback = (type: ToastType) => {
    try {
      if (type === 'error') {
        Vibration.vibrate([0, 30, 40, 30])
      } else if (type === 'warning') {
        Vibration.vibrate([0, 25])
      } else {
        Vibration.vibrate(15)
      }
    } catch {
      // Vibration not supported on current environment
    }
  }

  const showToast = useCallback(
    (options: ToastOptions | string, typeOverride?: ToastType): string => {
      const id = `mobile-toast-${Date.now()}-${Math.random().toString(36).substring(2, 9)}`

      let normalized: ToastOptions
      if (typeof options === 'string') {
        normalized = { message: options, type: typeOverride || 'info' }
      } else {
        normalized = { ...options, type: options.type || typeOverride || 'info' }
      }

      const toastType = normalized.type || 'info'
      triggerHapticFeedback(toastType)

      const newToast: ToastItemData = {
        id,
        title: normalized.title,
        message: normalized.message,
        type: toastType,
        duration: normalized.duration ?? DEFAULT_TOAST_DURATION,
        action: normalized.action,
        createdAt: Date.now(),
      }

      setToasts((prev) => [...prev.slice(-2), newToast])
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

export function useToast(): ToastContextValue {
  const context = useContext(ToastContext)
  if (!context) {
    throw new Error('useToast must be used within a ToastProvider')
  }
  return context
}
