import { useCallback, useEffect, useState } from 'react'

import { schedulingApi } from '@/api/scheduling'
import { getErrorMessage } from '@/api/client'
import type { Visit } from '@/api/types'
import { EmptyState, ErrorBanner, LoadingBlock } from '@/components/AsyncState'
import { PageHeader } from '@/components/PageHeader'
import { Button } from '@/components/ui/Button'
import { CancelVisitModal } from '@/components/ui/Modal'
import {
  addDays,
  formatDayLabel,
  parseDateInput,
  startOfDay,
  toDateInputValue,
} from '@/lib/scheduleTime'
import { DayCalendar } from '@/pages/schedule/DayCalendar'
import { VisitFormModal } from '@/pages/schedule/VisitFormModal'
import './SchedulePage.css'

export function SchedulePage() {
  const [day, setDay] = useState(() => startOfDay(new Date()))
  const [visits, setVisits] = useState<Visit[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [formOpen, setFormOpen] = useState(false)
  const [slotMinutes, setSlotMinutes] = useState(0)
  const [cancelTarget, setCancelTarget] = useState<Visit | null>(null)
  const [cancelBusy, setCancelBusy] = useState(false)
  const [reloadToken, setReloadToken] = useState(0)

  const dateIso = toDateInputValue(day)

  const reload = useCallback(() => {
    setReloadToken((value) => value + 1)
  }, [])

  useEffect(() => {
    let cancelled = false

    async function load() {
      setLoading(true)
      setError(null)
      try {
        const data = await schedulingApi.listVisitsForDate(dateIso)
        if (!cancelled) {
          setVisits(data)
        }
      } catch (err) {
        if (!cancelled) {
          setVisits([])
          setError(getErrorMessage(err, 'Nie udało się pobrać wizyt.'))
        }
      } finally {
        if (!cancelled) {
          setLoading(false)
        }
      }
    }

    void load()
    return () => {
      cancelled = true
    }
  }, [dateIso, reloadToken])

  function openCreate(minutesFromStart: number) {
    setSlotMinutes(minutesFromStart)
    setFormOpen(true)
  }

  async function confirmCancel(reason: string) {
    if (!cancelTarget) {
      return
    }
    setCancelBusy(true)
    setError(null)
    try {
      const updated = await schedulingApi.cancelVisit(cancelTarget.id, reason)
      setVisits((prev) => prev.map((visit) => (visit.id === updated.id ? updated : visit)))
      setCancelTarget(null)
    } catch (err) {
      setError(getErrorMessage(err, 'Nie udało się odwołać wizyty.'))
    } finally {
      setCancelBusy(false)
    }
  }

  return (
    <section className="schedule-page">
      <PageHeader
        title="Harmonogram"
        description="Widok dzienny — kliknij wolny slot, aby dodać wizytę, przeciągnij blok, aby zmienić godzinę."
        actions={
          <Button type="button" onClick={() => openCreate(60)}>
            + Nowa wizyta
          </Button>
        }
      />

      <div className="schedule-toolbar">
        <div className="schedule-toolbar__nav">
          <Button type="button" variant="secondary" size="sm" onClick={() => setDay((d) => addDays(d, -1))}>
            Poprzedni
          </Button>
          <Button
            type="button"
            variant="secondary"
            size="sm"
            onClick={() => setDay(startOfDay(new Date()))}
          >
            Dziś
          </Button>
          <Button type="button" variant="secondary" size="sm" onClick={() => setDay((d) => addDays(d, 1))}>
            Następny
          </Button>
        </div>

        <label className="schedule-toolbar__date">
          <span className="sr-only">Data</span>
          <input
            type="date"
            value={dateIso}
            onChange={(event) => setDay(parseDateInput(event.target.value))}
          />
        </label>

        <p className="schedule-toolbar__label">{formatDayLabel(day)}</p>
      </div>

      {error ? <ErrorBanner message={error} onRetry={reload} /> : null}

      {loading ? <LoadingBlock label="Ładowanie harmonogramu…" variant="panel" /> : null}

      {!loading && !error && visits.filter((v) => v.status !== 'CANCELLED').length === 0 ? (
        <EmptyState
          title="Brak wizyt tego dnia"
          description="Kliknij w siatkę godzin albo użyj „+ Nowa wizyta”."
          action={
            <Button type="button" size="sm" onClick={() => openCreate(60)}>
              + Nowa wizyta
            </Button>
          }
        />
      ) : null}

      {!loading && !error ? (
        <DayCalendar
          day={day}
          visits={visits}
          onVisitsChange={setVisits}
          onSlotClick={openCreate}
          onCancelVisit={setCancelTarget}
          onError={setError}
        />
      ) : null}

      <VisitFormModal
        open={formOpen}
        day={day}
        initialMinutes={slotMinutes}
        onClose={() => setFormOpen(false)}
        onCreated={reload}
      />

      <CancelVisitModal
        open={cancelTarget !== null}
        onClose={() => setCancelTarget(null)}
        onConfirm={confirmCancel}
        busy={cancelBusy}
      />
    </section>
  )
}
