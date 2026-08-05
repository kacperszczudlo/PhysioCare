import { useEffect, useMemo, useState, type FormEvent } from 'react'

import { schedulingApi } from '@/api/scheduling'
import { patientsApi } from '@/api/treatment'
import { ApiError } from '@/api/client'
import type { PatientSummary, TherapyType, VisitCreatePayload } from '@/api/types'
import { Button } from '@/components/ui/Button'
import { Field } from '@/components/ui/Field'
import { Modal } from '@/components/ui/Modal'
import { dateFromDayMinutes, formatTime, toIsoLocal } from '@/lib/scheduleTime'

interface VisitFormModalProps {
  open: boolean
  day: Date
  initialMinutes: number
  onClose: () => void
  onCreated: () => void
}

export function VisitFormModal({
  open,
  day,
  initialMinutes,
  onClose,
  onCreated,
}: VisitFormModalProps) {
  const [patients, setPatients] = useState<PatientSummary[]>([])
  const [therapyTypes, setTherapyTypes] = useState<TherapyType[]>([])
  const [loadingMeta, setLoadingMeta] = useState(false)
  const [patientId, setPatientId] = useState('')
  const [therapyTypeId, setTherapyTypeId] = useState('')
  const [startLocal, setStartLocal] = useState('')
  const [location, setLocation] = useState('')
  const [prep, setPrep] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  const [newTypeName, setNewTypeName] = useState('')
  const [newTypeColor, setNewTypeColor] = useState('#4a6b28')
  const [newTypeDuration, setNewTypeDuration] = useState(45)
  const [creatingType, setCreatingType] = useState(false)

  const selectedType = useMemo(
    () => therapyTypes.find((item) => item.id === therapyTypeId) ?? null,
    [therapyTypes, therapyTypeId],
  )

  useEffect(() => {
    if (!open) {
      return
    }

    const start = dateFromDayMinutes(day, initialMinutes)
    const local = `${String(start.getHours()).padStart(2, '0')}:${String(start.getMinutes()).padStart(2, '0')}`
    setStartLocal(local)
    setError(null)
    setLocation('')
    setPrep('')
    setBusy(false)

    let cancelled = false
    async function loadMeta() {
      setLoadingMeta(true)
      try {
        const [patientList, typeList] = await Promise.all([
          patientsApi.list(),
          schedulingApi.listTherapyTypes(),
        ])
        if (cancelled) {
          return
        }
        setPatients(patientList)
        setTherapyTypes(typeList)
        setPatientId((prev) => prev || patientList[0]?.id || '')
        setTherapyTypeId((prev) => prev || typeList[0]?.id || '')
      } catch (err) {
        if (!cancelled) {
          setError(
            err instanceof ApiError ? err.message : 'Nie udało się pobrać danych formularza.',
          )
        }
      } finally {
        if (!cancelled) {
          setLoadingMeta(false)
        }
      }
    }

    void loadMeta()
    return () => {
      cancelled = true
    }
  }, [open, day, initialMinutes])

  async function createTherapyType(event: FormEvent) {
    event.preventDefault()
    if (!newTypeName.trim()) {
      return
    }
    setCreatingType(true)
    setError(null)
    try {
      const created = await schedulingApi.createTherapyType({
        name: newTypeName.trim(),
        color_hex: newTypeColor,
        duration_min: newTypeDuration,
      })
      setTherapyTypes((prev) => [...prev, created])
      setTherapyTypeId(created.id)
      setNewTypeName('')
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Nie udało się dodać typu terapii.')
    } finally {
      setCreatingType(false)
    }
  }

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError(null)

    if (!patientId || !therapyTypeId || !selectedType) {
      setError('Wybierz pacjenta i typ terapii.')
      return
    }

    const [hours, minutes] = startLocal.split(':').map(Number)
    const start = new Date(day.getFullYear(), day.getMonth(), day.getDate(), hours, minutes, 0, 0)
    const end = new Date(start.getTime() + selectedType.duration_min * 60_000)

    const payload: VisitCreatePayload = {
      patient_id: patientId,
      therapy_type_id: therapyTypeId,
      start_at: toIsoLocal(start),
      end_at: toIsoLocal(end),
      location_address: location.trim(),
      prep_instructions: prep.trim(),
    }

    setBusy(true)
    try {
      await schedulingApi.createVisit(payload)
      onCreated()
      onClose()
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Nie udało się utworzyć wizyty.')
    } finally {
      setBusy(false)
    }
  }

  const endPreview = (() => {
    if (!selectedType || !startLocal) {
      return null
    }
    const [hours, minutes] = startLocal.split(':').map(Number)
    const start = new Date(day.getFullYear(), day.getMonth(), day.getDate(), hours, minutes, 0, 0)
    const end = new Date(start.getTime() + selectedType.duration_min * 60_000)
    return formatTime(end)
  })()

  return (
    <Modal open={open} title="Nowa wizyta" onClose={onClose}>
      {loadingMeta ? <p className="schedule-muted">Ładowanie…</p> : null}

      {!loadingMeta && patients.length === 0 ? (
        <p className="schedule-empty" role="status">
          Brak pacjentów w gabinecie. Pacjent musi najpierw zarejestrować się w aplikacji mobilnej z
          Twoim profilem terapeuty.
        </p>
      ) : null}

      {!loadingMeta && therapyTypes.length === 0 ? (
        <form className="ui-modal__form" onSubmit={(e) => void createTherapyType(e)}>
          <p className="schedule-muted">Najpierw dodaj typ terapii (kolor + domyślny czas).</p>
          <Field
            label="Nazwa typu"
            name="type_name"
            value={newTypeName}
            onChange={(e) => setNewTypeName(e.target.value)}
            required
          />
          <label className="ui-field">
            <span className="ui-field__label">Kolor</span>
            <input
              type="color"
              value={newTypeColor}
              onChange={(e) => setNewTypeColor(e.target.value)}
            />
          </label>
          <Field
            label="Czas trwania (min)"
            name="duration"
            type="number"
            min={15}
            step={15}
            value={String(newTypeDuration)}
            onChange={(e) => setNewTypeDuration(Number(e.target.value) || 45)}
          />
          {error ? (
            <p className="ui-modal__error" role="alert">
              {error}
            </p>
          ) : null}
          <Button type="submit" loading={creatingType}>
            Dodaj typ terapii
          </Button>
        </form>
      ) : null}

      {!loadingMeta && patients.length > 0 && therapyTypes.length > 0 ? (
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
            <span className="ui-field__label">Typ terapii</span>
            <select
              className="ui-modal__select"
              value={therapyTypeId}
              onChange={(e) => setTherapyTypeId(e.target.value)}
              required
            >
              {therapyTypes.map((type) => (
                <option key={type.id} value={type.id}>
                  {type.name} ({type.duration_min} min)
                </option>
              ))}
            </select>
          </label>

          <Field
            label="Start"
            name="start"
            type="time"
            step={900}
            value={startLocal}
            onChange={(e) => setStartLocal(e.target.value)}
            required
            hint={endPreview ? `Koniec: ${endPreview}` : undefined}
          />

          <Field
            label="Adres / lokalizacja"
            name="location"
            value={location}
            onChange={(e) => setLocation(e.target.value)}
          />

          <label className="ui-field">
            <span className="ui-field__label">Przygotowanie pacjenta</span>
            <textarea
              className="ui-modal__textarea"
              value={prep}
              onChange={(e) => setPrep(e.target.value)}
              rows={3}
            />
          </label>

          {error ? (
            <p className="ui-modal__error" role="alert">
              {error}
            </p>
          ) : null}

          <div className="ui-modal__actions">
            <Button type="button" variant="secondary" onClick={onClose} disabled={busy}>
              Anuluj
            </Button>
            <Button type="submit" loading={busy}>
              Zapisz wizytę
            </Button>
          </div>
        </form>
      ) : null}
    </Modal>
  )
}
