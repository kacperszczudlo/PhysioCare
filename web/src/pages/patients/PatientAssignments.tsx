import { useCallback, useEffect, useState, type FormEvent } from 'react'

import { exercisesApi } from '@/api/exercises'
import { getErrorMessage } from '@/api/client'
import type { ExerciseAssignment } from '@/api/types'
import { EmptyState, ErrorBanner, LoadingBlock, SuccessBanner } from '@/components/AsyncState'
import { Button } from '@/components/ui/Button'
import { DateCarousel } from '@/components/ui/DateCarousel'
import { Field } from '@/components/ui/Field'
import { Modal } from '@/components/ui/Modal'
import { AuthMediaPdfLink, AuthMediaVideo } from '@/components/AuthMedia'
import { getDosageError } from '@/lib/fieldPolicy'
import { addDays, parseDateInput, toDateInputValue } from '@/lib/scheduleTime'
import { AssignExerciseToPatientModal } from '@/pages/patients/AssignExerciseToPatientModal'
import './PatientAssignments.css'

interface PatientAssignmentsProps {
  patientId: string
  episodeId?: string | null
}

function formatPeriod(start: string, end: string): string {
  const fmt = new Intl.DateTimeFormat('pl-PL', { dateStyle: 'medium' })
  return `${fmt.format(parseDateInput(start))} - ${fmt.format(parseDateInput(end))}`
}

export function PatientAssignments({
  patientId,
  episodeId = null,
}: PatientAssignmentsProps) {
  const [items, setItems] = useState<ExerciseAssignment[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [assignOpen, setAssignOpen] = useState(false)
  const [editTarget, setEditTarget] = useState<ExerciseAssignment | null>(null)
  const [deleteTarget, setDeleteTarget] = useState<ExerciseAssignment | null>(null)
  const [dosage, setDosage] = useState('')
  const [startDate, setStartDate] = useState('')
  const [endDate, setEndDate] = useState('')
  const [busy, setBusy] = useState(false)
  const [formError, setFormError] = useState<string | null>(null)
  const [successMessage, setSuccessMessage] = useState<string | null>(null)

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await exercisesApi.listAssignments(patientId, { active: true })
      setItems(data)
    } catch (err) {
      setError(getErrorMessage(err, 'Nie udało się pobrać zaleceń.'))
      setItems([])
    } finally {
      setLoading(false)
    }
  }, [patientId])

  useEffect(() => {
    void load()
  }, [load])

  useEffect(() => {
    if (!successMessage) {
      return
    }
    const timer = window.setTimeout(() => setSuccessMessage(null), 5000)
    return () => window.clearTimeout(timer)
  }, [successMessage])

  function openEdit(assignment: ExerciseAssignment) {
    setEditTarget(assignment)
    setDosage(assignment.dosage)
    setStartDate(assignment.start_date)
    setEndDate(assignment.end_date)
    setFormError(null)
    setSuccessMessage(null)
  }

  async function onSave(event: FormEvent) {
    event.preventDefault()
    if (!editTarget) {
      return
    }
    const dosageError = getDosageError(dosage)
    if (dosageError) {
      setFormError(dosageError)
      return
    }
    setBusy(true)
    setFormError(null)
    try {
      const updated = await exercisesApi.updateAssignment(editTarget.id, {
        dosage: dosage.trim(),
        start_date: startDate,
        end_date: endDate,
      })
      setItems((prev) => prev.map((item) => (item.id === updated.id ? updated : item)))
      setEditTarget(null)
      setSuccessMessage('Zalecenie zostało zapisane.')
    } catch (err) {
      setFormError(getErrorMessage(err, 'Nie udało się zapisać zalecenia.'))
    } finally {
      setBusy(false)
    }
  }

  async function onDelete() {
    if (!deleteTarget) {
      return
    }
    setBusy(true)
    setFormError(null)
    try {
      await exercisesApi.deleteAssignment(deleteTarget.id)
      setItems((prev) => prev.filter((item) => item.id !== deleteTarget.id))
      setDeleteTarget(null)
      setSuccessMessage('Zalecenie zostało usunięte.')
    } catch (err) {
      setFormError(getErrorMessage(err, 'Nie udało się usunąć zalecenia.'))
    } finally {
      setBusy(false)
    }
  }

  return (
    <section className="patient-assignments" aria-label="Zalecenia ćwiczeń">
      <div className="patient-assignments__head">
        <div>
          <h2>Zalecenia ćwiczeń</h2>
          <p>Aktywne zalecenia widoczne u pacjenta w aplikacji.</p>
        </div>
        <div className="patient-assignments__head-actions">
          <Button type="button" size="sm" variant="secondary" onClick={() => void load()}>
            Odśwież
          </Button>
          <Button type="button" size="sm" onClick={() => setAssignOpen(true)}>
            Dodaj ćwiczenie
          </Button>
        </div>
      </div>

      {loading ? <LoadingBlock label="Ładowanie zaleceń…" /> : null}

      {!loading && error ? <ErrorBanner message={error} onRetry={() => void load()} /> : null}
      {successMessage ? <SuccessBanner message={successMessage} /> : null}

      {!loading && !error && items.length === 0 ? (
        <EmptyState
          title="Brak aktywnych ćwiczeń"
          description="Dodaj ćwiczenie z katalogu - pacjent zobaczy je od razu w aplikacji."
        />
      ) : null}

      {!loading && items.length > 0 ? (
        <ul className="patient-assignments__list">
          {items.map((assignment) => {
            return (
              <li key={assignment.id} className="patient-assignments__item">
                <div className="patient-assignments__meta">
                  <div className="patient-assignments__title-row">
                    <h3>{assignment.exercise_title}</h3>
                  </div>
                  <p className="patient-assignments__dosage">{assignment.dosage}</p>
                  <p className="patient-assignments__period">
                    {formatPeriod(assignment.start_date, assignment.end_date)}
                  </p>
                  {assignment.exercise_instruction ? (
                    <p className="patient-assignments__instruction">
                      {assignment.exercise_instruction}
                    </p>
                  ) : null}
                </div>
                <div className="patient-assignments__media">
                  {assignment.exercise_media_type === 'VIDEO' ? (
                    <AuthMediaVideo
                      path={assignment.exercise_file_url}
                      className="patient-assignments__player"
                    />
                  ) : null}
                  {assignment.exercise_media_type === 'PDF' ? (
                    <AuthMediaPdfLink
                      path={assignment.exercise_file_url}
                      className="patient-assignments__pdf"
                    >
                      Otwórz PDF
                    </AuthMediaPdfLink>
                  ) : null}
                  <div className="patient-assignments__actions">
                    <Button
                      type="button"
                      size="sm"
                      variant="secondary"
                      onClick={() => openEdit(assignment)}
                    >
                      Edytuj
                    </Button>
                    <Button
                      type="button"
                      size="sm"
                      variant="ghost"
                      onClick={() => {
                        setFormError(null)
                        setDeleteTarget(assignment)
                      }}
                    >
                      Usuń
                    </Button>
                  </div>
                </div>
              </li>
            )
          })}
        </ul>
      ) : null}

      <AssignExerciseToPatientModal
        open={assignOpen}
        patientId={patientId}
        episodeId={episodeId}
        onClose={() => setAssignOpen(false)}
        onAssigned={() => {
          setSuccessMessage('Ćwiczenie zostało przypisane.')
          void load()
        }}
      />

      <Modal
        open={editTarget !== null}
        title="Edytuj zalecenie"
        description={
          editTarget ? `„${editTarget.exercise_title}” - dawkowanie i okres.` : undefined
        }
        onClose={() => setEditTarget(null)}
      >
        <form className="ui-modal__form" onSubmit={(e) => void onSave(e)}>
          <Field
            label="Dawkowanie"
            name="dosage"
            value={dosage}
            onChange={(e) => setDosage(e.target.value)}
            required
          />
          <div className="patient-assignments__dates">
            <DateCarousel
              label="Od"
              value={startDate}
              onChange={setStartDate}
              minimumDate={toDateInputValue(addDays(new Date(), -90))}
              dayCount={180}
              required
            />
            <DateCarousel
              label="Do"
              value={endDate}
              onChange={setEndDate}
              minimumDate={startDate}
              dayCount={180}
              required
            />
          </div>
          {formError ? (
            <p className="ui-modal__error" role="alert">
              {formError}
            </p>
          ) : null}
          <div className="ui-modal__actions">
            <Button
              type="button"
              variant="secondary"
              onClick={() => setEditTarget(null)}
              disabled={busy}
            >
              Anuluj
            </Button>
            <Button type="submit" loading={busy}>
              Zapisz
            </Button>
          </div>
        </form>
      </Modal>

      <Modal
        open={deleteTarget !== null}
        title="Usuń zalecenie"
        description={
          deleteTarget
            ? `„${deleteTarget.exercise_title}” zniknie z listy pacjenta. Ćwiczenie w katalogu zostanie.`
            : undefined
        }
        onClose={() => setDeleteTarget(null)}
      >
        <div className="ui-modal__form">
          {formError ? (
            <p className="ui-modal__error" role="alert">
              {formError}
            </p>
          ) : null}
          <div className="ui-modal__actions">
            <Button
              type="button"
              variant="secondary"
              onClick={() => setDeleteTarget(null)}
              disabled={busy}
            >
              Anuluj
            </Button>
            <Button type="button" onClick={() => void onDelete()} loading={busy}>
              Usuń zalecenie
            </Button>
          </div>
        </div>
      </Modal>
    </section>
  )
}
