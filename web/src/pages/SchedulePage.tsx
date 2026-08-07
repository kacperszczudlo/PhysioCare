import { useCallback, useEffect, useMemo, useState } from 'react'

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
  formatTime,
  startOfDay,
  toDateInputValue,
} from '@/lib/scheduleTime'
import { DayCarousel } from '@/components/ui/DayCarousel'
import { DayCalendar } from '@/pages/schedule/DayCalendar'
import { VisitFormModal } from '@/pages/schedule/VisitFormModal'
import './SchedulePage.css'

function formatPendingWhen(iso: string): string {
  const date = new Date(iso)
  return new Intl.DateTimeFormat('pl-PL', {
    weekday: 'short',
    day: 'numeric',
    month: 'short',
    hour: '2-digit',
    minute: '2-digit',
  }).format(date)
}

export function SchedulePage() {
  const [day, setDay] = useState(() => startOfDay(new Date()))
  const [visits, setVisits] = useState<Visit[]>([])
  const [pendingAll, setPendingAll] = useState<Visit[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [formOpen, setFormOpen] = useState(false)
  const [slotMinutes, setSlotMinutes] = useState(0)
  const [editTarget, setEditTarget] = useState<Visit | null>(null)
  const [cancelTarget, setCancelTarget] = useState<Visit | null>(null)
  const [cancelBusy, setCancelBusy] = useState(false)
  const [actionBusyId, setActionBusyId] = useState<string | null>(null)
  const [showPendingList, setShowPendingList] = useState(false)
  const [reloadToken, setReloadToken] = useState(0)
  const [didAutoFocusPending, setDidAutoFocusPending] = useState(false)

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
        const [dayVisits, pending] = await Promise.all([
          schedulingApi.listVisitsForDate(dateIso),
          schedulingApi.listPendingVisits(),
        ])
        if (!cancelled) {
          setVisits(dayVisits)
          setPendingAll(pending)

          if (!didAutoFocusPending && pending.length > 0) {
            const soonest = [...pending].sort(
              (a, b) => new Date(a.start_at).getTime() - new Date(b.start_at).getTime(),
            )[0]
            const pendingDay = startOfDay(new Date(soonest.start_at))
            if (toDateInputValue(pendingDay) !== dateIso) {
              setDidAutoFocusPending(true)
              setDay(pendingDay)
              return
            }
            setDidAutoFocusPending(true)
          }
        }
      } catch (err) {
        if (!cancelled) {
          setVisits([])
          setPendingAll([])
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
  }, [dateIso, reloadToken, didAutoFocusPending])

  const pendingSorted = useMemo(
    () =>
      [...pendingAll].sort(
        (a, b) => new Date(a.start_at).getTime() - new Date(b.start_at).getTime(),
      ),
    [pendingAll],
  )

  const pendingOnDay = useMemo(
    () => pendingSorted.filter((visit) => toDateInputValue(new Date(visit.start_at)) === dateIso),
    [pendingSorted, dateIso],
  )

  function openCreate(minutesFromStart: number) {
    setEditTarget(null)
    setSlotMinutes(minutesFromStart)
    setFormOpen(true)
  }

  function openEdit(visit: Visit) {
    setEditTarget(visit)
    setFormOpen(true)
  }

  function closeForm() {
    setFormOpen(false)
    setEditTarget(null)
  }

  function applyVisitUpdate(updated: Visit) {
    setVisits((prev) => {
      const sameDay = toDateInputValue(new Date(updated.start_at)) === dateIso
      if (updated.status === 'CANCELLED' || !sameDay) {
        return prev.filter((visit) => visit.id !== updated.id)
      }
      const exists = prev.some((visit) => visit.id === updated.id)
      if (!exists) {
        return [...prev, updated]
      }
      return prev.map((visit) => (visit.id === updated.id ? updated : visit))
    })
    setPendingAll((prev) =>
      updated.status === 'PENDING_APPROVAL'
        ? prev.map((visit) => (visit.id === updated.id ? updated : visit))
        : prev.filter((visit) => visit.id !== updated.id),
    )
  }

  async function approveVisit(visit: Visit) {
    setActionBusyId(visit.id)
    setError(null)
    try {
      const updated = await schedulingApi.approveVisit(visit.id)
      applyVisitUpdate(updated)
    } catch (err) {
      setError(getErrorMessage(err, 'Nie udało się zatwierdzić zgłoszenia.'))
    } finally {
      setActionBusyId(null)
    }
  }

  async function rejectVisit(visit: Visit) {
    setActionBusyId(visit.id)
    setError(null)
    try {
      const updated = await schedulingApi.rejectVisit(visit.id)
      applyVisitUpdate(updated)
    } catch (err) {
      setError(getErrorMessage(err, 'Nie udało się odrzucić zgłoszenia.'))
    } finally {
      setActionBusyId(null)
    }
  }

  async function confirmCancel(reason: string) {
    if (!cancelTarget) {
      return
    }
    setCancelBusy(true)
    setError(null)
    try {
      const updated = await schedulingApi.cancelVisit(cancelTarget.id, reason)
      applyVisitUpdate(updated)
      setCancelTarget(null)
    } catch (err) {
      setError(getErrorMessage(err, 'Nie udało się odwołać wizyty.'))
    } finally {
      setCancelBusy(false)
    }
  }

  function jumpToVisitDay(visit: Visit) {
    setDay(startOfDay(new Date(visit.start_at)))
    setShowPendingList(false)
  }

  return (
    <section className="schedule-page">
      <PageHeader
        title="Harmonogram"
        description="Widok dzienny — kliknij wolny slot, aby dodać wizytę, przeciągnij blok, aby zmienić godzinę, lub Edytuj, aby zmienić treść wizyty. Zgłoszenia pacjentów widać jako bloki „Do zatwierdzenia”."
        actions={
          <Button type="button" onClick={() => openCreate(60)}>
            + Nowa wizyta
          </Button>
        }
      />

      {pendingSorted.length > 0 ? (
        <div className="schedule-pending-banner" role="status">
          <div className="schedule-pending-banner__copy">
            <p className="schedule-pending-banner__title">
              {pendingSorted.length === 1
                ? '1 zgłoszenie oczekuje na zatwierdzenie'
                : pendingSorted.length >= 2 && pendingSorted.length <= 4
                  ? `${pendingSorted.length} zgłoszenia oczekują na zatwierdzenie`
                  : `${pendingSorted.length} zgłoszeń oczekuje na zatwierdzenie`}
            </p>
            <p className="schedule-pending-banner__meta">
              {pendingOnDay.length > 0
                ? 'Widać je na kalendarzu poniżej ze statusem „Do zatwierdzenia”.'
                : 'Najbliższe zgłoszenie otworzyło odpowiedni dzień — zatwierdź na kalendarzu lub z listy.'}
            </p>
          </div>
          <Button
            type="button"
            variant="secondary"
            size="sm"
            onClick={() => setShowPendingList((value) => !value)}
            aria-expanded={showPendingList}
          >
            {showPendingList ? 'Ukryj listę' : 'Pokaż listę'}
          </Button>
        </div>
      ) : null}

      {showPendingList && pendingSorted.length > 0 ? (
        <div className="schedule-pending-list">
          {pendingSorted.map((visit) => {
            const onThisDay = toDateInputValue(new Date(visit.start_at)) === dateIso
            return (
              <div key={visit.id} className="schedule-pending-item">
                <div className="schedule-pending-item__main">
                  <p className="schedule-pending-item__title">
                    {visit.patient_first_name} {visit.patient_last_name} · {visit.therapy_type_name}
                  </p>
                  <p className="schedule-pending-item__meta">
                    {formatPendingWhen(visit.start_at)} · {formatTime(new Date(visit.start_at))}–
                    {formatTime(new Date(visit.end_at))}
                    {onThisDay ? ' · na tym dniu' : ''}
                  </p>
                </div>
                <div className="schedule-pending-item__actions">
                  {!onThisDay ? (
                    <Button
                      type="button"
                      size="sm"
                      variant="secondary"
                      onClick={() => jumpToVisitDay(visit)}
                    >
                      Przejdź do dnia
                    </Button>
                  ) : null}
                  <Button
                    type="button"
                    size="sm"
                    loading={actionBusyId === visit.id}
                    onClick={() => void approveVisit(visit)}
                  >
                    Zatwierdź
                  </Button>
                  <Button
                    type="button"
                    size="sm"
                    variant="secondary"
                    disabled={actionBusyId === visit.id}
                    onClick={() => void rejectVisit(visit)}
                  >
                    Odrzuć
                  </Button>
                  <Button
                    type="button"
                    size="sm"
                    variant="secondary"
                    onClick={() => openEdit(visit)}
                  >
                    Szczegóły
                  </Button>
                </div>
              </div>
            )
          })}
        </div>
      ) : null}

      <div className="schedule-toolbar">
        <div className="schedule-toolbar__nav">
          <Button
            type="button"
            variant="secondary"
            size="sm"
            onClick={() => setDay((d) => addDays(d, -1))}
          >
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
          <Button
            type="button"
            variant="secondary"
            size="sm"
            onClick={() => setDay((d) => addDays(d, 1))}
          >
            Następny
          </Button>
        </div>

        <p className="schedule-toolbar__label">{formatDayLabel(day)}</p>

        <div className="schedule-toolbar__carousel">
          <DayCarousel
            label="Wybierz dzień"
            value={day}
            onChange={setDay}
            minimumDate={addDays(startOfDay(new Date()), -60)}
            dayCount={120}
          />
        </div>
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
          onEditVisit={openEdit}
          onCancelVisit={setCancelTarget}
          onApproveVisit={(visit) => void approveVisit(visit)}
          onRejectVisit={(visit) => void rejectVisit(visit)}
          onError={setError}
        />
      ) : null}

      <VisitFormModal
        open={formOpen}
        day={day}
        initialMinutes={slotMinutes}
        visit={editTarget}
        onClose={closeForm}
        onCreated={reload}
        onUpdated={(updated) => {
          applyVisitUpdate(updated)
        }}
        onRejected={(updated) => {
          applyVisitUpdate(updated)
        }}
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
