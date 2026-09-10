import { useEffect, useMemo, useState, type CSSProperties, type FormEvent } from 'react'

import { schedulingApi } from '@/api/scheduling'
import { patientsApi } from '@/api/treatment'
import { ApiError } from '@/api/client'
import type {
  PatientSummary,
  TherapyType,
  TherapyTypePreset,
  Visit,
  VisitCreatePayload,
  VisitUpdatePayload,
} from '@/api/types'
import { Button } from '@/components/ui/Button'
import { DayCarousel } from '@/components/ui/DayCarousel'
import { Modal } from '@/components/ui/Modal'
import { TimeCarousel } from '@/components/ui/TimeCarousel'
import { addDays, dateFromDayMinutes, formatTime, startOfDay, toIsoLocal } from '@/lib/scheduleTime'

import './VisitFormModal.css'

interface VisitFormModalProps {
  open: boolean
  day: Date
  initialMinutes: number
  visit?: Visit | null
  onClose: () => void
  onCreated: () => void
  onUpdated?: (visit: Visit) => void
  onRejected?: (visit: Visit) => void
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

function timeLocalFromDate(value: Date): string {
  return `${String(value.getHours()).padStart(2, '0')}:${String(value.getMinutes()).padStart(2, '0')}`
}

export function VisitFormModal({
  open,
  day,
  initialMinutes,
  visit = null,
  onClose,
  onCreated,
  onUpdated,
  onRejected,
}: VisitFormModalProps) {
  const isEdit = visit != null
  const isPending = visit?.status === 'PENDING_APPROVAL'

  const [patients, setPatients] = useState<PatientSummary[]>([])
  const [options, setOptions] = useState<VisitTypeOption[]>([])
  const [loadingMeta, setLoadingMeta] = useState(false)
  const [patientId, setPatientId] = useState('')
  const [therapyTypeId, setTherapyTypeId] = useState('')
  const [formDay, setFormDay] = useState(() => startOfDay(day))
  const [startLocal, setStartLocal] = useState('')
  const [prep, setPrep] = useState('')
  const [patientSummary, setPatientSummary] = useState('')
  const [location, setLocation] = useState('')
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

    setError(null)
    setBusy(false)

    if (visit) {
      const start = new Date(visit.start_at)
      setFormDay(startOfDay(start))
      setStartLocal(timeLocalFromDate(start))
      setPrep(visit.prep_instructions || '')
      setPatientSummary(visit.patient_summary || '')
      setLocation(visit.location_address || '')
      setPatientId(visit.patient)
      setTherapyTypeId(visit.therapy_type)
    } else {
      const start = dateFromDayMinutes(day, initialMinutes)
      setFormDay(startOfDay(day))
      setStartLocal(timeLocalFromDate(start))
      setPrep('')
      setPatientSummary('')
      setLocation('')
      setPatientId('')
      setTherapyTypeId('')
    }

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

        if (visit?.therapy_type && !nextOptions.some((item) => item.id === visit.therapy_type)) {
          const current = typeList.find((type) => type.id === visit.therapy_type)
          if (current) {
            nextOptions.unshift({
              ...current,
              group: 'kind',
              description: 'Aktualny typ wizyty',
            })
          }
        }

        setPatients(patientList)
        setOptions(nextOptions)

        if (visit) {
          setPatientId(visit.patient)
          setTherapyTypeId(visit.therapy_type)
        } else {
          setPatientId(patientList[0]?.id || '')
          setTherapyTypeId(nextOptions[0]?.id || '')
        }
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
  }, [open, day, initialMinutes, visit])

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError(null)

    if (!therapyTypeId || !selectedType) {
      setError('Wybierz typ wizyty.')
      return
    }

    if (!isEdit && !patientId) {
      setError('Wybierz pacjenta.')
      return
    }

    const [hours, minutes] = startLocal.split(':').map(Number)
    const start = new Date(
      formDay.getFullYear(),
      formDay.getMonth(),
      formDay.getDate(),
      hours,
      minutes,
      0,
      0,
    )
    const end = new Date(start.getTime() + selectedType.duration_min * 60_000)

    setBusy(true)
    try {
      if (visit && isPending) {
        const payload: VisitUpdatePayload = {
          therapy_type_id: therapyTypeId,
          start_at: toIsoLocal(start),
          end_at: toIsoLocal(end),
          prep_instructions: prep.trim(),
          location_address: location.trim(),
        }
        const updated = await schedulingApi.approveVisit(visit.id, payload)
        onUpdated?.(updated)
        onClose()
      } else if (visit) {
        const payload: VisitUpdatePayload = {
          therapy_type_id: therapyTypeId,
          start_at: toIsoLocal(start),
          end_at: toIsoLocal(end),
          prep_instructions: prep.trim(),
          patient_summary: patientSummary.trim(),
          location_address: location.trim(),
        }
        const updated = await schedulingApi.updateVisit(visit.id, payload)
        onUpdated?.(updated)
        onClose()
      } else {
        const payload: VisitCreatePayload = {
          patient_id: patientId,
          therapy_type_id: therapyTypeId,
          start_at: toIsoLocal(start),
          end_at: toIsoLocal(end),
          prep_instructions: prep.trim(),
        }
        await schedulingApi.createVisit(payload)
        onCreated()
        onClose()
      }
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.message
          : isPending
            ? 'Nie udało się zatwierdzić zgłoszenia.'
            : isEdit
              ? 'Nie udało się zapisać zmian wizyty.'
              : 'Nie udało się utworzyć wizyty.',
      )
    } finally {
      setBusy(false)
    }
  }

  async function onReject() {
    if (!visit || !isPending) {
      return
    }
    setBusy(true)
    setError(null)
    try {
      const updated = await schedulingApi.rejectVisit(visit.id)
      onRejected?.(updated)
      onClose()
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Nie udało się odrzucić zgłoszenia.')
    } finally {
      setBusy(false)
    }
  }

  const endPreview = (() => {
    if (!selectedType || !startLocal) {
      return null
    }
    const [hours, minutes] = startLocal.split(':').map(Number)
    const start = new Date(
      formDay.getFullYear(),
      formDay.getMonth(),
      formDay.getDate(),
      hours,
      minutes,
      0,
      0,
    )
    const end = new Date(start.getTime() + selectedType.duration_min * 60_000)
    return formatTime(end)
  })()

  const dayPickerMin = addDays(startOfDay(new Date()), -14)

  const patientLabel = visit
    ? `${visit.patient_first_name} ${visit.patient_last_name}`.trim()
    : null

  const showForm = isEdit || (!loadingMeta && patients.length > 0)

  return (
    <Modal
      open={open}
      title={isPending ? 'Zgłoszenie wizyty' : isEdit ? 'Edytuj wizytę' : 'Nowa wizyta'}
      description={
        isPending
          ? 'Pacjent zgłosił termin. Możesz skorygować szczegóły i zatwierdzić albo odrzucić zgłoszenie.'
          : isEdit
            ? 'Zmień typ, godzinę, przygotowanie lub adres wizyty.'
            : 'Wybierz typ wizyty klikając kafelek - przy każdej wizycie osobno.'
      }
      size="lg"
      onClose={onClose}
    >
      {loadingMeta ? <p className="schedule-muted">Ładowanie…</p> : null}

      {!loadingMeta && !isEdit && patients.length === 0 ? (
        <p className="schedule-empty" role="status">
          Brak pacjentów w gabinecie. Pacjent musi najpierw zarejestrować się w aplikacji mobilnej z
          Twoim profilem fizjoterapeuty.
        </p>
      ) : null}

      {!loadingMeta && showForm ? (
        <form className="ui-modal__form" onSubmit={(e) => void onSubmit(e)}>
          {isEdit ? (
            <label className="ui-field">
              <span className="ui-field__label">Pacjent</span>
              <input className="ui-modal__select" value={patientLabel || ''} disabled readOnly />
            </label>
          ) : (
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
          )}

          <fieldset className="visit-type-picker">
            <legend className="ui-field__label">Typ wizyty</legend>
            {optionsByGroup.map((group) => (
              <div key={group.group} className="visit-type-picker__group">
                <p className="visit-type-picker__group-label">{group.label}</p>
                <div
                  className="visit-type-picker__tiles"
                  role="radiogroup"
                  aria-label={group.label}
                >
                  {group.items.map((type) => {
                    const selected = type.id === therapyTypeId
                    return (
                      <button
                        key={type.id}
                        type="button"
                        role="radio"
                        aria-checked={selected}
                        className={
                          selected ? 'visit-type-tile visit-type-tile--selected' : 'visit-type-tile'
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

          <DayCarousel
            label="Dzień"
            value={formDay}
            onChange={setFormDay}
            minimumDate={dayPickerMin}
            dayCount={56}
          />

          <TimeCarousel
            label="Start"
            value={startLocal}
            onChange={setStartLocal}
            required
            hint={endPreview ? `Koniec: ${endPreview}` : undefined}
          />

          {visit?.patient_note ? (
            <div className="ui-field">
              <span className="ui-field__label">Notatka pacjenta</span>
              <p className="schedule-muted" style={{ margin: 0, whiteSpace: 'pre-wrap' }}>
                {visit.patient_note}
              </p>
            </div>
          ) : null}

          <label className="ui-field">
            <span className="ui-field__label">Przygotowanie pacjenta</span>
            <textarea
              className="ui-modal__textarea"
              value={prep}
              onChange={(e) => setPrep(e.target.value)}
              rows={3}
              placeholder="Np. wygodny strój, wyniki badań…"
            />
          </label>

          {isEdit && !isPending ? (
            <label className="ui-field">
              <span className="ui-field__label">Podsumowanie dla pacjenta</span>
              <textarea
                className="ui-modal__textarea"
                value={patientSummary}
                onChange={(e) => setPatientSummary(e.target.value)}
                rows={4}
                placeholder="Prosty język: co było na wizycie, co robić w domu, na co uważać…"
              />
              <span className="ui-field__hint">
                Widoczne w aplikacji pacjenta. Notatki kliniczne epizodu pozostają tylko u Ciebie.
              </span>
            </label>
          ) : null}

          {isEdit ? (
            <label className="ui-field">
              <span className="ui-field__label">Adres wizyty</span>
              <textarea
                className="ui-modal__textarea"
                value={location}
                onChange={(e) => setLocation(e.target.value)}
                rows={2}
                placeholder="Adres gabinetu lub wizyty domowej"
              />
            </label>
          ) : null}

          {error ? (
            <p className="ui-modal__error" role="alert">
              {error}
            </p>
          ) : null}

          <div className="ui-modal__actions">
            <Button type="button" variant="secondary" onClick={onClose} disabled={busy}>
              Anuluj
            </Button>
            {isPending ? (
              <Button
                type="button"
                variant="secondary"
                onClick={() => void onReject()}
                disabled={busy}
              >
                Odrzuć
              </Button>
            ) : null}
            <Button type="submit" loading={busy} disabled={!therapyTypeId}>
              {isPending ? 'Zatwierdź' : isEdit ? 'Zapisz zmiany' : 'Zapisz wizytę'}
            </Button>
          </div>
        </form>
      ) : null}
    </Modal>
  )
}
