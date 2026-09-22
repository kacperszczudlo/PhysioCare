import { useEffect, useState, type FormEvent } from 'react'

import { exercisesApi } from '@/api/exercises'
import { treatmentApi } from '@/api/treatment'
import { ApiError } from '@/api/client'
import type { Exercise, ExerciseAssignment, TreatmentEpisode } from '@/api/types'
import { Button } from '@/components/ui/Button'
import { DateCarousel } from '@/components/ui/DateCarousel'
import { Field } from '@/components/ui/Field'
import { Modal } from '@/components/ui/Modal'
import { getDosageError } from '@/lib/fieldPolicy'
import { toDateInputValue } from '@/lib/scheduleTime'

const DEFAULT_DOSAGE = '3 serie × 10 powtórzeń'
const OVERLAP_MESSAGE =
  'To ćwiczenie jest już przypisane temu pacjentowi w nakładającym się okresie.'

function defaultEndDate(): string {
  const end = new Date()
  end.setDate(end.getDate() + 14)
  return toDateInputValue(end)
}

function rangesOverlap(aStart: string, aEnd: string, bStart: string, bEnd: string): boolean {
  return aStart <= bEnd && aEnd >= bStart
}

function isExerciseBlocked(
  exerciseId: string,
  assignments: ExerciseAssignment[],
  startDate: string,
  endDate: string,
): boolean {
  return assignments.some(
    (item) =>
      item.exercise === exerciseId &&
      rangesOverlap(item.start_date, item.end_date, startDate, endDate),
  )
}

interface AssignExerciseToPatientModalProps {
  open: boolean
  patientId: string
  episodeId?: string | null
  onClose: () => void
  onAssigned: () => void
}

/**
 * Modal wyboru ćwiczenia z bazy i przypisywania go bezpośrednio w karcie konkretnego pacjenta.
 */
export function AssignExerciseToPatientModal({
  open,
  patientId,
  episodeId: preferredEpisodeId = null,
  onClose,
  onAssigned,
}: AssignExerciseToPatientModalProps) {
  const [query, setQuery] = useState('')
  const [debouncedQuery, setDebouncedQuery] = useState('')
  const [results, setResults] = useState<Exercise[]>([])
  const [existingAssignments, setExistingAssignments] = useState<ExerciseAssignment[]>([])
  const [selected, setSelected] = useState<Exercise | null>(null)
  const [episodes, setEpisodes] = useState<TreatmentEpisode[]>([])
  const [episodeId, setEpisodeId] = useState('')
  const [dosage, setDosage] = useState(DEFAULT_DOSAGE)
  const [startDate, setStartDate] = useState(toDateInputValue(new Date()))
  const [endDate, setEndDate] = useState(defaultEndDate)
  const [searching, setSearching] = useState(false)
  const [loadingEpisodes, setLoadingEpisodes] = useState(false)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!open) {
      return
    }
    setQuery('')
    setDebouncedQuery('')
    setResults([])
    setSelected(null)
    setDosage(DEFAULT_DOSAGE)
    setStartDate(toDateInputValue(new Date()))
    setEndDate(defaultEndDate())
    setBusy(false)
    setError(null)
    setEpisodeId(preferredEpisodeId ?? '')
  }, [open, patientId, preferredEpisodeId])

  useEffect(() => {
    const timer = window.setTimeout(() => setDebouncedQuery(query.trim()), 250)
    return () => window.clearTimeout(timer)
  }, [query])

  useEffect(() => {
    if (!open || !patientId) {
      setExistingAssignments([])
      return
    }
    let cancelled = false
    async function loadAssignments() {
      try {
        const list = await exercisesApi.listAssignments(patientId)
        if (!cancelled) {
          setExistingAssignments(list)
        }
      } catch {
        if (!cancelled) {
          setExistingAssignments([])
        }
      }
    }
    void loadAssignments()
    return () => {
      cancelled = true
    }
  }, [open, patientId])

  useEffect(() => {
    if (!open || !patientId) {
      setEpisodes([])
      return
    }
    let cancelled = false
    async function loadEpisodes() {
      setLoadingEpisodes(true)
      try {
        const list = await treatmentApi.listEpisodes(patientId)
        if (cancelled) {
          return
        }
        setEpisodes(list)
        const preferred =
          preferredEpisodeId && list.some((item) => item.id === preferredEpisodeId)
            ? preferredEpisodeId
            : (list[0]?.id ?? '')
        setEpisodeId(preferred)
      } catch {
        if (!cancelled) {
          setEpisodes([])
          setEpisodeId('')
        }
      } finally {
        if (!cancelled) {
          setLoadingEpisodes(false)
        }
      }
    }
    void loadEpisodes()
    return () => {
      cancelled = true
    }
  }, [open, patientId, preferredEpisodeId])

  useEffect(() => {
    if (!open || selected) {
      return
    }
    let cancelled = false
    async function search() {
      setSearching(true)
      setError(null)
      try {
        const page = await exercisesApi.list({ q: debouncedQuery || undefined, page: 1 })
        if (!cancelled) {
          setResults(page.results.slice(0, 12))
        }
      } catch (err) {
        if (!cancelled) {
          setResults([])
          setError(err instanceof ApiError ? err.message : 'Nie udało się pobrać katalogu ćwiczeń.')
        }
      } finally {
        if (!cancelled) {
          setSearching(false)
        }
      }
    }
    void search()
    return () => {
      cancelled = true
    }
  }, [open, debouncedQuery, selected])

  useEffect(() => {
    if (selected && isExerciseBlocked(selected.id, existingAssignments, startDate, endDate)) {
      setSelected(null)
      setError(OVERLAP_MESSAGE)
    }
  }, [selected, existingAssignments, startDate, endDate])

  const blockedExerciseIds = new Set(
    results
      .filter((exercise) => isExerciseBlocked(exercise.id, existingAssignments, startDate, endDate))
      .map((exercise) => exercise.id),
  )

  async function onSubmit(event: FormEvent) {
    event.preventDefault()
    if (!selected) {
      setError('Wybierz ćwiczenie z listy.')
      return
    }
    if (isExerciseBlocked(selected.id, existingAssignments, startDate, endDate)) {
      setError(OVERLAP_MESSAGE)
      return
    }
    const dosageError = getDosageError(dosage)
    if (dosageError) {
      setError(dosageError)
      return
    }
    setBusy(true)
    setError(null)
    try {
      await exercisesApi.assign({
        exercise_id: selected.id,
        patient_id: patientId,
        episode_id: episodeId || null,
        dosage: dosage.trim(),
        start_date: startDate,
        end_date: endDate,
      })
      onAssigned()
      onClose()
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Nie udało się przypisać ćwiczenia.')
    } finally {
      setBusy(false)
    }
  }

  return (
    <Modal open={open} title="Dodaj ćwiczenie" onClose={onClose}>
      <form className="ui-modal__form" onSubmit={(e) => void onSubmit(e)}>
        {!selected ? (
          <div className="assign-to-patient__picker">
            <Field
              label="Szukaj w katalogu"
              name="exercise_query"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Nazwa ćwiczenia…"
              autoComplete="off"
            />
            {searching ? (
              <p className="assign-to-patient__hint" role="status">
                Szukam…
              </p>
            ) : null}
            {!searching && results.length === 0 ? (
              <p className="assign-to-patient__hint" role="status">
                Brak ćwiczeń spełniających kryteria.
              </p>
            ) : null}
            {results.length > 0 ? (
              <ul className="assign-to-patient__results" role="listbox" aria-label="Wyniki">
                {results.map((exercise) => {
                  const blocked = blockedExerciseIds.has(exercise.id)
                  return (
                    <li key={exercise.id}>
                      <button
                        type="button"
                        className={
                          blocked
                            ? 'assign-to-patient__result assign-to-patient__result--blocked'
                            : 'assign-to-patient__result'
                        }
                        role="option"
                        aria-disabled={blocked}
                        disabled={blocked}
                        onClick={() => {
                          setSelected(exercise)
                          setError(null)
                        }}
                      >
                        <span className="assign-to-patient__result-title">{exercise.title}</span>
                        <span className="assign-to-patient__result-meta">
                          {blocked
                            ? 'Już w tym okresie'
                            : exercise.media_type === 'VIDEO'
                              ? 'Wideo'
                              : 'PDF'}
                        </span>
                      </button>
                    </li>
                  )
                })}
              </ul>
            ) : null}
          </div>
        ) : (
          <div className="assign-to-patient__selected">
            <div>
              <p className="assign-to-patient__selected-label">Wybrane ćwiczenie</p>
              <p className="assign-to-patient__selected-title">{selected.title}</p>
            </div>
            <Button
              type="button"
              size="sm"
              variant="secondary"
              onClick={() => {
                setSelected(null)
                setError(null)
              }}
              disabled={busy}
            >
              Zmień
            </Button>
          </div>
        )}

        <label className="ui-field">
          <span className="ui-field__label">Epizod (opcjonalnie)</span>
          <select
            className="ui-modal__select"
            value={episodeId}
            onChange={(e) => setEpisodeId(e.target.value)}
            disabled={loadingEpisodes || busy}
          >
            <option value="">Bez epizodu</option>
            {episodes.map((episode) => (
              <option key={episode.id} value={episode.id}>
                {episode.icd10_code || 'Bez ICD-10'} · {episode.status}
              </option>
            ))}
          </select>
        </label>

        <Field
          label="Dawkowanie"
          name="dosage"
          value={dosage}
          onChange={(e) => setDosage(e.target.value)}
          required
          disabled={busy}
        />

        <div className="patient-assignments__dates">
          <DateCarousel
            label="Od"
            value={startDate}
            onChange={setStartDate}
            minimumDate={toDateInputValue(new Date())}
            dayCount={90}
            required
          />
          <DateCarousel
            label="Do"
            value={endDate}
            onChange={setEndDate}
            minimumDate={startDate}
            dayCount={120}
            required
          />
        </div>

        {error ? (
          <p className="ui-modal__error" role="alert">
            {error}
          </p>
        ) : null}

        <div className="ui-modal__actions">
          <Button type="button" variant="secondary" onClick={onClose} disabled={busy}>
            Anuluj
          </Button>
          <Button type="submit" loading={busy} disabled={!selected}>
            Wyślij do aplikacji
          </Button>
        </div>
      </form>
    </Modal>
  )
}
