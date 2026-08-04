import { useEffect, useId, useRef, type FormEvent, type ReactNode } from 'react'

import { Button } from '@/components/ui/Button'
import './Modal.css'

interface ModalProps {
  open: boolean
  title: string
  onClose: () => void
  children: ReactNode
}

export function Modal({ open, title, onClose, children }: ModalProps) {
  const dialogRef = useRef<HTMLDialogElement>(null)
  const titleId = useId()

  useEffect(() => {
    const dialog = dialogRef.current
    if (!dialog) {
      return
    }
    if (open && !dialog.open) {
      dialog.showModal()
    } else if (!open && dialog.open) {
      dialog.close()
    }
  }, [open])

  return (
    <dialog
      ref={dialogRef}
      className="ui-modal"
      aria-labelledby={titleId}
      onClose={onClose}
      onClick={(event) => {
        if (event.target === dialogRef.current) {
          onClose()
        }
      }}
    >
      <div className="ui-modal__panel">
        <header className="ui-modal__header">
          <h2 id={titleId}>{title}</h2>
          <button type="button" className="ui-modal__close" onClick={onClose} aria-label="Zamknij">
            ×
          </button>
        </header>
        <div className="ui-modal__body">{children}</div>
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
