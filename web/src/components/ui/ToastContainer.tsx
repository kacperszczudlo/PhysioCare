import './Toast.css'
import { useToast } from './ToastContext'
import { ToastItem } from './ToastItem'

/**
 * Kontener wyrenderowanych powiadomień tosterowych wyświetlanych w rogu ekranu.
 */
export function ToastContainer() {
  const { toasts, removeToast } = useToast()

  if (toasts.length === 0) return null

  return (
    <div className="toast-container" aria-label="Powiadomienia">
      {toasts.map((toast) => (
        <ToastItem key={toast.id} toast={toast} onClose={removeToast} />
      ))}
    </div>
  )
}
