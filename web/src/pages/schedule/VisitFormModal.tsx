import { useEffect, useMemo, useState, type CSSProperties, type FormEvent } from 'react'

import { schedulingApi } from '@/api/scheduling'
import { patientsApi } from '@/api/treatment'
import { ApiError } from '@/api/client'
import type {
  PatientSummary,
  TherapyType,
  TherapyTypePreset,
  VisitCreatePayload,
} from '@/api/types'
import { Button } from '@/components/ui/Button'
import { Field } from '@/components/ui/Field'
import { Modal } from '@/components/ui/Modal'
import { dateFromDayMinutes, formatTime, toIsoLocal } from '@/lib/scheduleTime'

import './VisitFormModal.css'

interface VisitFormModalProps {
  open: boolean
  day: Date
  initialMinutes: number
  onClose: () => void
  onCreated: () => void
}

const GROUP_ORDER: TherapyTypePreset['group'][] = ['kind', 'profile']

const GROUP_LABEL: Record<TherapyTypePreset['group'], string> = {
  kind: 'Główne typy wizyt',
  profile: 'Profil / specjalizacja',
}

type VisitTypeOption = TherapyType & {
  group: TherapyTypePreset['group']
  description: string
}

export function VisitFormModal({
  open,
  day,
  initialMinutes,
  onClose,
  onCreated,
}: VisitFormModalProps) {
  const [patients, setPatients] = useState<PatientSummary[]>([])
  const [options, setOptions] = useState<VisitTypeOption[]>([])
  const [loadingMeta, setLoadingMeta] = useState(false)
  const [patientId, setPatientId] = useState('')
  const [therapyTypeId, setTherapyTypeId] = useState('')
  const [startLocal, setStartLocal] = useState('')
  const [prep, setPrep] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  const selectedType = useMemo(
    () => options.find((item) => item.id === therapyTypeId) ?? null,
    [options, therapyTypeId],
  )

  const optionsByGroup = useMemo(
    () =>
      GROUP_ORDER.map((group) => ({
        group,
        label: GROUP_LABEL[group],
        items: options.filter((item) => item.group === group),
      })).filter((entry) => entry.items.length > 0),
    [options],
  )

  useEffect(() => {
    if (!open) {
      return
    }

    const start = dateFromDayMinutes(day, initialMinutes)
    const local = `${String(start.getHours()).padStart(2, '0')}:${String(start.getMinutes()).padStart(2, '0')}`
    setStartLocal(local)
    setError(null)
    setPrep('')
    setBusy(false)
    setPatientId('')
    setTherapyTypeId('')

    let cancelled = false
    async function loadMeta() {
      setLoadingMeta(true)
      try {
        const [patientList, typeList, presetList] = await Promise.all([
          patientsApi.list(),
          schedulingApi.seedTherapyTypePresets(),
          schedulingApi.listTherapyTypePresets(),
        ])
        if (cancelled) {
          return
        }

        const byName = new Map(typeList.map((type) => [type.name, type]))
        const nextOptions: VisitTypeOption[] = []
        for (const preset of presetList) {
          const type = byName.get(preset.name)
          if (!type) {
            continue
          }
          nextOptions.push({
            ...type,
            group: preset.group,
            description: preset.description,
            color_hex: preset.color_hex || type.color_hex,
            duration_min: type.duration_min || preset.duration_min,
          })
        }

        setPatients(patientList)
        setOptions(nextOptions)
        setPatientId(patientList[0]?.id || '')
        setTherapyTypeId(nextOptions[0]?.id || '')
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

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError(null)

    if (!patientId || !therapyTypeId || !selectedType) {
      setError('Wybierz pacjenta i typ wizyty.')
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
    <Modal
      open={open}
      title="Nowa wizyta"
      description="Wybierz typ wizyty klikając kafelek — przy każdej wizycie osobno."
      size="lg"
      onClose={onClose}
    >
      {loadingMeta ? <p className="schedule-muted">Ładowanie…</p> : null}

      {!loadingMeta && patients.length === 0 ? (
        <p className="schedule-empty" role="status">
          Brak pacjentów w gabinecie. Pacjent musi najpierw zarejestrować się w aplikacji mobilnej z
          Twoim profilem terapeuty.
        </p>
      ) : null}

      {!loadingMeta && patients.length > 0 ? (
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

          <fieldset className="visit-type-picker">
            <legend className="ui-field__label">Typ wizyty</legend>
            {optionsByGroup.map((group) => (
              <div key={group.group} className="visit-type-picker__group">
                <p className="visit-type-picker__group-label">{group.label}</p>
                <div className="visit-type-picker__tiles" role="radiogroup" aria-label={group.label}>
                  {group.items.map((type) => {
                    const selected = type.id === therapyTypeId
                    return (
                      <button
                        key={type.id}
                        type="button"
                        role="radio"
                        aria-checked={selected}
                        className={
                          selected
                            ? 'visit-type-tile visit-type-tile--selected'
                            : 'visit-type-tile'
                        }
                        title={type.description}
                        onClick={() => setTherapyTypeId(type.id)}
                        style={{ '--tile-color': type.color_hex } as CSSProperties}
                      >
                        <span className="visit-type-tile__dot" aria-hidden />
                        <span className="visit-type-tile__body">
                          <span className="visit-type-tile__name">{type.name}</span>
                          <span className="visit-type-tile__meta">{type.duration_min} min</span>
                          <span className="visit-type-tile__desc">{type.description}</span>
                        </span>
                      </button>
                    )
                  })}
                </div>
              </div>
            ))}
          </fieldset>

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
            <Button type="submit" loading={busy} disabled={!therapyTypeId}>
              Zapisz wizytę
            </Button>
          </div>
        </form>
      ) : null}
    </Modal>
  )
}
