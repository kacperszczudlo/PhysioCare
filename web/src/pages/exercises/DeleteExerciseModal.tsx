import { useEffect, useState } from 'react'

import { exercisesApi } from '@/api/exercises'
import { getErrorMessage } from '@/api/client'
import type { Exercise } from '@/api/types'
import { Button } from '@/components/ui/Button'
import { Modal } from '@/components/ui/Modal'

interface DeleteExerciseModalProps {
  open: boolean
  exercise: Exercise | null
  onClose: () => void
  onDeleted: () => void
}

/**
 * Modal potwierdzenia usunięcia ćwiczenia z bazy z informacją o wyczyszczeniu powiązanych zaleceń.
 */
export function DeleteExerciseModal({
  open,
  exercise,
  onClose,
  onDeleted,
}: DeleteExerciseModalProps) {
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (open) {
      setBusy(false)
      setError(null)
    }
  }, [open, exercise?.id])

  async function onConfirm() {
    if (!exercise) {
      return
    }
    setBusy(true)
    setError(null)
    try {
      await exercisesApi.remove(exercise.id)
      onDeleted()
      onClose()
    } catch (err) {
      setError(getErrorMessage(err, 'Nie udało się usunąć ćwiczenia.'))
    } finally {
      setBusy(false)
    }
  }

  return (
    <Modal
      open={open}
      title="Usuń ćwiczenie"
      description={
        exercise
          ? `„${exercise.title}” zniknie z katalogu. Przypisania do pacjentów też zostaną usunięte.`
          : undefined
      }
      onClose={onClose}
    >
      <div className="ui-modal__form">
        {error ? (
          <p className="ui-modal__error" role="alert">
            {error}
          </p>
        ) : null}
        <div className="ui-modal__actions">
          <Button type="button" variant="secondary" onClick={onClose} disabled={busy}>
            Anuluj
          </Button>
          <Button type="button" onClick={() => void onConfirm()} loading={busy}>
            Usuń
          </Button>
        </div>
      </div>
    </Modal>
  )
}
