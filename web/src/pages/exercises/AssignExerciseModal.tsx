import { useEffect, useState, type FormEvent } from 'react'

import { exercisesApi } from '@/api/exercises'
import { patientsApi, treatmentApi } from '@/api/treatment'
import { ApiError } from '@/api/client'
import type { Exercise, PatientSummary, TreatmentEpisode } from '@/api/types'
import { SuccessBanner } from '@/components/AsyncState'
import { Button } from '@/components/ui/Button'
import { DateCarousel } from '@/components/ui/DateCarousel'
import { Field } from '@/components/ui/Field'
import { Modal } from '@/components/ui/Modal'
import { toDateInputValue } from '@/lib/scheduleTime'

interface AssignExerciseModalProps {
  open: boolean
  exercise: Exercise | null
  onClose: () => void
  onAssigned: () => void
}

export function AssignExerciseModal({
  open,
  exercise,
  onClose,
  onAssigned,
}: AssignExerciseModalProps) {
  const [patients, setPatients] = useState<PatientSummary[]>([])
  const [episodes, setEpisodes] = useState<TreatmentEpisode[]>([])
  const [patientId, setPatientId] = useState('')
  const [episodeId, setEpisodeId] = useState('')
  const [dosage, setDosage] = useState('3 serie × 10 powtórzeń')
  const [startDate, setStartDate] = useState(toDateInputValue(new Date()))
  const [endDate, setEndDate] = useState(() => {
    const end = new Date()
    end.setDate(end.getDate() + 14)
    return toDateInputValue(end)
  })
  const [loadingMeta, setLoadingMeta] = useState(false)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)

  useEffect(() => {
    if (!open) {
      return
    }
    setError(null)
    setSuccess(null)
    setBusy(false)
    setDosage('3 serie × 10 powtórzeń')
    setStartDate(toDateInputValue(new Date()))
    const end = new Date()
    end.setDate(end.getDate() + 14)
    setEndDate(toDateInputValue(end))

    let cancelled = false
    async function load() {
      setLoadingMeta(true)
      try {
        const list = await patientsApi.list()
        if (cancelled) {
          return
        }
        setPatients(list)
        setPatientId(list[0]?.id ?? '')
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof ApiError ? err.message : 'Nie udało się pobrać pacjentów.')
        }
      } finally {
        if (!cancelled) {
          setLoadingMeta(false)
        }
      }
    }
    void load()
    return () => {
      cancelled = true
    }
  }, [open])

  useEffect(() => {
    if (!open || !patientId) {
      setEpisodes([])
      setEpisodeId('')
      return
    }
    let cancelled = false
    async function loadEpisodes() {
      try {
        const list = await treatmentApi.listEpisodes(patientId)
        if (cancelled) {
          return
        }
        setEpisodes(list)
        setEpisodeId(list[0]?.id ?? '')
      } catch {
        if (!cancelled) {
          setEpisodes([])
          setEpisodeId('')
        }
      }
    }
    void loadEpisodes()
    return () => {
      cancelled = true
    }
  }, [open, patientId])

  async function onSubmit(event: FormEvent) {
    event.preventDefault()
    if (!exercise || !patientId) {
      return
    }
    setBusy(true)
    setError(null)
    setSuccess(null)
    try {
      await exercisesApi.assign({
        exercise_id: exercise.id,
        patient_id: patientId,
        episode_id: episodeId || null,
        dosage: dosage.trim(),
        start_date: startDate,
        end_date: endDate,
      })
      setSuccess('Wysłano do aplikacji pacjenta.')
      onAssigned()
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Nie udało się przypisać ćwiczenia.')
    } finally {
      setBusy(false)
    }
  }

  return (
    <Modal
      open={open}
      title={exercise ? `Przypisz: ${exercise.title}` : 'Przypisz ćwiczenie'}
      onClose={onClose}
    >
      {loadingMeta ? <p className="exercises-muted">Ładowanie…</p> : null}

      {!loadingMeta && patients.length === 0 ? (
        <p className="exercises-empty" role="status">
          Brak pacjentów — nie ma komu przypisać ćwiczenia.
        </p>
      ) : null}

      {!loadingMeta && patients.length > 0 && exercise ? (
        <form className="ui-modal__form" onSubmit={(e) => void onSubmit(e)}>
          <label className="ui-field">
            <span className="ui-field__label">Pacjent</span>
            <select
              className="ui-modal__select"
              value={patientId}
              onChange={(e) => setPatientId(e.target.value)}
              required
            >
              {patients.map((patient) => (
                <option key={patient.id} value={patient.id}>
                  {patient.first_name} {patient.last_name}
                </option>
              ))}
            </select>
          </label>

          <label className="ui-field">
            <span className="ui-field__label">Epizod (opcjonalnie)</span>
            <select
              className="ui-modal__select"
              value={episodeId}
              onChange={(e) => setEpisodeId(e.target.value)}
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
          />
          <div className="exercises-date-row">
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
          {success ? <SuccessBanner message={success} /> : null}

          <div className="ui-modal__actions">
            <Button type="button" variant="secondary" onClick={onClose} disabled={busy}>
              Zamknij
            </Button>
            <Button type="submit" loading={busy}>
              Wyślij do aplikacji
            </Button>
          </div>
        </form>
      ) : null}
    </Modal>
  )
}
