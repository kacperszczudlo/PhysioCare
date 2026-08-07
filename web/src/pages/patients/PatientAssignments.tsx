import { useCallback, useEffect, useState, type FormEvent } from 'react'

import { exercisesApi } from '@/api/exercises'
import { getErrorMessage } from '@/api/client'
import type { ExerciseAssignment } from '@/api/types'
import { EmptyState, LoadingBlock } from '@/components/AsyncState'
import { Button } from '@/components/ui/Button'
import { DateCarousel } from '@/components/ui/DateCarousel'
import { Field } from '@/components/ui/Field'
import { Modal } from '@/components/ui/Modal'
import { resolveMediaUrl } from '@/lib/mediaUrl'
import { addDays, parseDateInput, toDateInputValue } from '@/lib/scheduleTime'
import './PatientAssignments.css'

interface PatientAssignmentsProps {
  patientId: string
}

function formatPeriod(start: string, end: string): string {
  const fmt = new Intl.DateTimeFormat('pl-PL', { dateStyle: 'medium' })
  return `${fmt.format(parseDateInput(start))} – ${fmt.format(parseDateInput(end))}`
}

function isActive(assignment: ExerciseAssignment): boolean {
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  const start = parseDateInput(assignment.start_date)
  const end = parseDateInput(assignment.end_date)
  return start <= today && end >= today
}

export function PatientAssignments({ patientId }: PatientAssignmentsProps) {
  const [items, setItems] = useState<ExerciseAssignment[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [editTarget, setEditTarget] = useState<ExerciseAssignment | null>(null)
  const [deleteTarget, setDeleteTarget] = useState<ExerciseAssignment | null>(null)
  const [dosage, setDosage] = useState('')
  const [startDate, setStartDate] = useState('')
  const [endDate, setEndDate] = useState('')
  const [busy, setBusy] = useState(false)
  const [formError, setFormError] = useState<string | null>(null)

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await exercisesApi.listAssignments(patientId)
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

  function openEdit(assignment: ExerciseAssignment) {
    setEditTarget(assignment)
    setDosage(assignment.dosage)
    setStartDate(assignment.start_date)
    setEndDate(assignment.end_date)
    setFormError(null)
  }

  async function onSave(event: FormEvent) {
    event.preventDefault()
    if (!editTarget) {
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
          <p>Okres, dawkowanie i materiał widoczny u pacjenta w aplikacji.</p>
        </div>
        <Button type="button" size="sm" variant="secondary" onClick={() => void load()}>
          Odśwież
        </Button>
      </div>

      {loading ? <LoadingBlock label="Ładowanie zaleceń…" /> : null}

      {!loading && error ? <p className="patient-assignments__error">{error}</p> : null}

      {!loading && !error && items.length === 0 ? (
        <EmptyState
          title="Brak przypisanych ćwiczeń"
          description="Przypisz ćwiczenie z katalogu „Ćwiczenia”, a pojawi się tutaj do edycji okresu i usunięcia."
        />
      ) : null}

      {!loading && items.length > 0 ? (
        <ul className="patient-assignments__list">
          {items.map((assignment) => {
            const mediaUrl = resolveMediaUrl(assignment.exercise_file_url)
            return (
              <li key={assignment.id} className="patient-assignments__item">
                <div className="patient-assignments__meta">
                  <div className="patient-assignments__title-row">
                    <h3>{assignment.exercise_title}</h3>
                    {isActive(assignment) ? (
                      <span className="patient-assignments__badge">Aktywne</span>
                    ) : (
                      <span className="patient-assignments__badge patient-assignments__badge--muted">
                        Poza okresem
                      </span>
                    )}
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
                  {mediaUrl && assignment.exercise_media_type === 'VIDEO' ? (
                    <video
                      className="patient-assignments__player"
                      src={mediaUrl}
                      controls
                      preload="metadata"
                    />
                  ) : null}
                  {mediaUrl && assignment.exercise_media_type === 'PDF' ? (
                    <a
                      className="patient-assignments__pdf"
                      href={mediaUrl}
                      target="_blank"
                      rel="noreferrer"
                    >
                      Otwórz PDF
                    </a>
                  ) : null}
                  <div className="patient-assignments__actions">
                    <Button type="button" size="sm" variant="secondary" onClick={() => openEdit(assignment)}>
                      Okres
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

      <Modal
        open={editTarget !== null}
        title="Edytuj zalecenie"
        description={editTarget ? `„${editTarget.exercise_title}” — dawkowanie i okres.` : undefined}
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
            <Button type="button" variant="secondary" onClick={() => setEditTarget(null)} disabled={busy}>
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
            <Button type="button" variant="secondary" onClick={() => setDeleteTarget(null)} disabled={busy}>
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
