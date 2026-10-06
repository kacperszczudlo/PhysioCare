import { useEffect, useId, useRef, type FormEvent, type ReactNode } from 'react'

import { Button } from '@/components/ui/Button'
import './Modal.css'

/** Właściwości komponentu okna dialogowego Modal. */
interface ModalProps {
  /** Czy okno modalne jest widoczne. */
  open: boolean
  /** Tytuł nagłówkowy okna dialogowego. */
  title: string
  /** Opcjonalny opis pomocniczy dialogu. */
  description?: string
  /** Szerokość/rozmiar panelu (md, lg, xl). */
  size?: 'md' | 'lg' | 'xl'
  /** Opcjonalna klasa kontenera dialogu. */
  className?: string
  /** Opcjonalna klasa ciała modala. */
  bodyClassName?: string
  /** Callback zamknij okno. */
  onClose: () => void
  /** Treść widoku lub formularza umieszczona w ciele dialogu. */
  children: ReactNode
}

/**
 * Komponent okna dialogowego/modalnego oparty o natywny znacznik `<dialog>` HTML5.
 *
 * Wspiera zamknięcie klawiszem ESC, kliknięciem w tło (backdrop), powrót fokusu
 * do elementu wywołującego oraz pełną dostępność WCAG (`aria-labelledby`, `aria-describedby`).
 *
 * @example
 * <Modal open={isOpen} title="Dodaj wizytę" onClose={closeModal}>
 *   <VisitForm />
 * </Modal>
 */
export function Modal({
  open,
  title,
  description,
  size = 'md',
  className = '',
  bodyClassName = '',
  onClose,
  children,
}: ModalProps) {
  const dialogRef = useRef<HTMLDialogElement>(null)
  const previousActiveElement = useRef<HTMLElement | null>(null)
  const titleId = useId()
  const descriptionId = useId()

  useEffect(() => {
    const dialog = dialogRef.current
    if (!dialog) {
      return
    }
    if (open) {
      if (document.activeElement instanceof HTMLElement) {
        previousActiveElement.current = document.activeElement
      }
      if (!dialog.open) {
        dialog.showModal()
      }
    } else if (!open && dialog.open) {
      dialog.close()
      previousActiveElement.current?.focus()
    }
  }, [open])

  const handleClose = () => {
    onClose()
    previousActiveElement.current?.focus()
  }

  return (
    <dialog
      ref={dialogRef}
      className={`ui-modal ${className}`.trim()}
      aria-labelledby={titleId}
      aria-describedby={description ? descriptionId : undefined}
      onCancel={(e) => {
        e.preventDefault()
        handleClose()
      }}
      onClose={handleClose}
      onClick={(event) => {
        if (event.target === dialogRef.current) {
          handleClose()
        }
      }}
    >
      <div className={`ui-modal__panel ui-modal__panel--${size}`}>
        <header className="ui-modal__header">
          <div className="ui-modal__heading">
            <h2 id={titleId}>{title}</h2>
            {description ? (
              <p id={descriptionId} className="ui-modal__description">
                {description}
              </p>
            ) : null}
          </div>
          <button
            type="button"
            className="ui-modal__close"
            onClick={handleClose}
            aria-label="Zamknij okno"
          >
            ×
          </button>
        </header>
        <div className={`ui-modal__body ${bodyClassName}`.trim()}>{children}</div>
      </div>
    </dialog>
  )
}

interface ConfirmCancelProps {
  open: boolean
  onClose: () => void
  onConfirm: (reason: string) => Promise<void>
  busy?: boolean
}

export function CancelVisitModal({ open, onClose, onConfirm, busy }: ConfirmCancelProps) {
  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const form = new FormData(event.currentTarget)
    await onConfirm(String(form.get('reason') ?? ''))
  }

  return (
    <Modal open={open} title="Odwołaj wizytę" onClose={onClose}>
      <form className="ui-modal__form" onSubmit={(e) => void onSubmit(e)}>
        <label className="ui-field">
          <span className="ui-field__label">Powód (opcjonalnie)</span>
          <textarea className="ui-modal__textarea" name="reason" rows={3} />
        </label>
        <div className="ui-modal__actions">
          <Button type="button" variant="secondary" onClick={onClose} disabled={busy}>
            Anuluj
          </Button>
          <Button type="submit" loading={busy}>
            Odwołaj wizytę
          </Button>
        </div>
      </form>
    </Modal>
  )
}
