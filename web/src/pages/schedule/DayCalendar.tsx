import {
  useEffect,
  useRef,
  useState,
  type MouseEvent,
  type PointerEvent as ReactPointerEvent,
} from 'react'

import { schedulingApi } from '@/api/scheduling'
import { ApiError } from '@/api/client'
import type { Visit } from '@/api/types'
import {
  DAY_END_HOUR,
  DAY_START_HOUR,
  PX_PER_MINUTE,
  SNAP_MINUTES,
  clamp,
  dateFromDayMinutes,
  dayBounds,
  formatTime,
  hourMarks,
  minutesFromDayStart,
  slotOffsets,
  snapMinutes,
  toIsoLocal,
} from '@/lib/scheduleTime'
import { getPolishHolidayName } from '@/lib/holidays'
import './DayCalendar.css'

interface DayCalendarProps {
  day: Date
  visits: Visit[]
  onVisitsChange: (visits: Visit[]) => void
  onSlotClick: (minutesFromStart: number) => void
  onEditVisit: (visit: Visit) => void
  onCancelVisit: (visit: Visit) => void
  onApproveVisit?: (visit: Visit) => void
  onRejectVisit?: (visit: Visit) => void
  onError: (message: string | null) => void
}

interface DragState {
  visitId: string
  durationMin: number
  originMinutes: number
  pointerOffsetMin: number
  currentMinutes: number
}

function lineKind(minutes: number): 'hour' | 'half' | 'quarter' {
  if (minutes % 60 === 0) {
    return 'hour'
  }
  if (minutes % 30 === 0) {
    return 'half'
  }
  return 'quarter'
}

/**
 * Komponent kalendarza dziennego wizyt z osią czasu, podglądem na żywo i przeciąganiem bloków czasowych.
 */
export function DayCalendar({
  day,
  visits,
  onVisitsChange,
  onSlotClick,
  onEditVisit,
  onCancelVisit,
  onApproveVisit,
  onRejectVisit,
  onError,
}: DayCalendarProps) {
  const gridRef = useRef<HTMLDivElement>(null)
  const visitsRef = useRef(visits)
  const dragRef = useRef<DragState | null>(null)
  const [drag, setDrag] = useState<DragState | null>(null)
  const [savingId, setSavingId] = useState<string | null>(null)
  const [hoverMinutes, setHoverMinutes] = useState<number | null>(null)
  const { minutes: dayMinutes } = dayBounds(day)
  const gridHeight = dayMinutes * PX_PER_MINUTE
  const gridSlots = slotOffsets(day).slice(0, -1)

  visitsRef.current = visits
  dragRef.current = drag

  useEffect(() => {
    if (!drag) {
      return
    }

    function onPointerMove(event: PointerEvent) {
      const current = dragRef.current
      const grid = gridRef.current
      if (!current || !grid) {
        return
      }
      const rect = grid.getBoundingClientRect()
      const raw = (event.clientY - rect.top) / PX_PER_MINUTE - current.pointerOffsetMin
      const maxStart = dayMinutes - current.durationMin
      const next = clamp(snapMinutes(raw), 0, Math.max(0, maxStart))
      setDrag({ ...current, currentMinutes: next })
    }

    async function onPointerUp() {
      const current = dragRef.current
      setDrag(null)
      if (!current || current.currentMinutes === current.originMinutes) {
        return
      }

      const start = dateFromDayMinutes(day, current.currentMinutes)
      const end = new Date(start.getTime() + current.durationMin * 60_000)
      const previous = visitsRef.current
      const optimistic = previous.map((visit) =>
        visit.id === current.visitId
          ? { ...visit, start_at: toIsoLocal(start), end_at: toIsoLocal(end) }
          : visit,
      )
      onVisitsChange(optimistic)
      setSavingId(current.visitId)
      onError(null)

      try {
        const updated = await schedulingApi.updateVisitTimes(
          current.visitId,
          toIsoLocal(start),
          toIsoLocal(end),
        )
        onVisitsChange(
          visitsRef.current.map((visit) => (visit.id === updated.id ? updated : visit)),
        )
      } catch (err) {
        onVisitsChange(previous)
        onError(err instanceof ApiError ? err.message : 'Nie udało się przesunąć wizyty.')
      } finally {
        setSavingId(null)
      }
    }

    window.addEventListener('pointermove', onPointerMove)
    window.addEventListener('pointerup', onPointerUp)
    return () => {
      window.removeEventListener('pointermove', onPointerMove)
      window.removeEventListener('pointerup', onPointerUp)
    }
  }, [drag, day, dayMinutes, onVisitsChange, onError])

  function minutesFromClientY(clientY: number): number {
    const grid = gridRef.current
    if (!grid) {
      return 0
    }
    const rect = grid.getBoundingClientRect()
    return clamp(snapMinutes((clientY - rect.top) / PX_PER_MINUTE), 0, dayMinutes - SNAP_MINUTES)
  }

  function beginDrag(visit: Visit, event: ReactPointerEvent<HTMLElement>) {
    if (visit.status === 'CANCELLED' || savingId) {
      return
    }
    event.preventDefault()
    event.stopPropagation()
    setHoverMinutes(null)

    const grid = gridRef.current
    if (!grid) {
      return
    }

    const start = new Date(visit.start_at)
    const end = new Date(visit.end_at)
    const originMinutes = minutesFromDayStart(start, day)
    const durationMin = Math.max((end.getTime() - start.getTime()) / 60_000, SNAP_MINUTES)
    const rect = grid.getBoundingClientRect()
    const pointerOffsetMin = (event.clientY - rect.top) / PX_PER_MINUTE - originMinutes

    setDrag({
      visitId: visit.id,
      durationMin,
      originMinutes,
      pointerOffsetMin,
      currentMinutes: originMinutes,
    })
  }

  function handleGridPointerMove(event: ReactPointerEvent<HTMLDivElement>) {
    if (drag || savingId) {
      setHoverMinutes(null)
      return
    }
    const target = event.target as HTMLElement
    if (!target.closest('.day-cal__lane') || target.closest('.day-cal__event')) {
      setHoverMinutes(null)
      return
    }
    setHoverMinutes(minutesFromClientY(event.clientY))
  }

  function handleGridPointerLeave() {
    setHoverMinutes(null)
  }

  function handleGridClick(event: MouseEvent<HTMLDivElement>) {
    if (drag || savingId) {
      return
    }
    const target = event.target as HTMLElement
    if (!target.closest('.day-cal__lane') || target.closest('.day-cal__event')) {
      return
    }
    onSlotClick(minutesFromClientY(event.clientY))
  }

  const visibleVisits = visits.filter((visit) => visit.status !== 'CANCELLED')
  const hoverLabel =
    hoverMinutes !== null ? formatTime(dateFromDayMinutes(day, hoverMinutes)) : null
  const holidayName = getPolishHolidayName(day)

  return (
    <div className="day-cal-wrapper">
      {holidayName ? (
        <div className="day-cal__holiday-banner" role="status">
          <span>
            <strong>Dzień wolny od pracy ({holidayName}).</strong> Domyślne godziny z grafiku
            cyklicznego są w tym dniu wyłączone.
          </span>
        </div>
      ) : null}
      <div className="day-cal" style={{ ['--day-cal-height' as string]: `${gridHeight}px` }}>
        <div className="day-cal__hours" aria-hidden="true">
          {hourMarks(day).map((mark) => {
            const top = minutesFromDayStart(mark, day) * PX_PER_MINUTE
            return (
              <div key={mark.toISOString()} className="day-cal__hour" style={{ top }}>
                {formatTime(mark)}
              </div>
            )
          })}
          {hoverMinutes !== null && hoverLabel ? (
            <div
              className="day-cal__hover-time"
              style={{ top: hoverMinutes * PX_PER_MINUTE + (SNAP_MINUTES * PX_PER_MINUTE) / 2 }}
            >
              {hoverLabel}
            </div>
          ) : null}
        </div>

        <div
          ref={gridRef}
          className="day-cal__track"
          role="grid"
          aria-label={`Harmonogram ${DAY_START_HOUR}:00-${DAY_END_HOUR}:00, sloty co ${SNAP_MINUTES} min`}
          onClick={handleGridClick}
          onPointerMove={handleGridPointerMove}
          onPointerLeave={handleGridPointerLeave}
        >
          <div className="day-cal__lane">
            {gridSlots.map((minutes) => {
              const kind = lineKind(minutes)
              return (
                <div
                  key={minutes}
                  className={`day-cal__line day-cal__line--${kind}`}
                  style={{ top: minutes * PX_PER_MINUTE }}
                />
              )
            })}

            {hoverMinutes !== null && !drag ? (
              <div
                className="day-cal__slot-preview"
                style={{
                  top: hoverMinutes * PX_PER_MINUTE,
                  height: SNAP_MINUTES * PX_PER_MINUTE,
                }}
                aria-hidden="true"
              />
            ) : null}

            {visibleVisits.map((visit) => {
              const start = new Date(visit.start_at)
              const end = new Date(visit.end_at)
              const isDragging = drag?.visitId === visit.id
              const isPending = visit.status === 'PENDING_APPROVAL'
              const topMinutes = isDragging ? drag.currentMinutes : minutesFromDayStart(start, day)
              const durationMin = Math.max((end.getTime() - start.getTime()) / 60_000, SNAP_MINUTES)
              const color = visit.therapy_type_color || '#4a6b28'
              const displayStart = isDragging ? dateFromDayMinutes(day, topMinutes) : start
              const displayEnd = new Date(displayStart.getTime() + durationMin * 60_000)

              return (
                <article
                  key={visit.id}
                  className={[
                    'day-cal__event',
                    isPending ? 'day-cal__event--pending' : '',
                    savingId === visit.id ? 'day-cal__event--saving' : '',
                    isDragging ? 'day-cal__event--dragging' : '',
                  ]
                    .filter(Boolean)
                    .join(' ')}
                  style={{
                    top: topMinutes * PX_PER_MINUTE,
                    height: Math.max(durationMin * PX_PER_MINUTE, isPending ? 68 : 56),
                    backgroundColor: color,
                  }}
                  aria-label={
                    isPending
                      ? `Zgłoszenie: ${visit.patient_first_name} ${visit.patient_last_name}, ${visit.therapy_type_name}`
                      : undefined
                  }
                  onPointerDown={(event) => beginDrag(visit, event)}
                >
                  <div className="day-cal__event-body">
                    <p className="day-cal__event-time">
                      {formatTime(displayStart)} - {formatTime(displayEnd)}
                      {isPending ? (
                        <span className="day-cal__event-badge">Do zatwierdzenia</span>
                      ) : null}
                    </p>
                    <p className="day-cal__event-title">
                      {visit.patient_first_name} {visit.patient_last_name}
                    </p>
                    <p className="day-cal__event-meta">{visit.therapy_type_name}</p>
                  </div>
                  <div className="day-cal__event-actions">
                    {isPending ? (
                      <>
                        <button
                          type="button"
                          className="day-cal__event-action day-cal__event-action--primary"
                          onClick={(event) => {
                            event.stopPropagation()
                            onApproveVisit?.(visit)
                          }}
                          onPointerDown={(event) => event.stopPropagation()}
                        >
                          Zatwierdź
                        </button>
                        <button
                          type="button"
                          className="day-cal__event-action"
                          onClick={(event) => {
                            event.stopPropagation()
                            onRejectVisit?.(visit)
                          }}
                          onPointerDown={(event) => event.stopPropagation()}
                        >
                          Odrzuć
                        </button>
                      </>
                    ) : null}
                    <button
                      type="button"
                      className="day-cal__event-action"
                      onClick={(event) => {
                        event.stopPropagation()
                        onEditVisit(visit)
                      }}
                      onPointerDown={(event) => event.stopPropagation()}
                    >
                      {isPending ? 'Szczegóły' : 'Edytuj'}
                    </button>
                    {!isPending ? (
                      <button
                        type="button"
                        className="day-cal__event-action"
                        onClick={(event) => {
                          event.stopPropagation()
                          onCancelVisit(visit)
                        }}
                        onPointerDown={(event) => event.stopPropagation()}
                      >
                        Odwołaj
                      </button>
                    ) : null}
                  </div>
                </article>
              )
            })}
          </div>
        </div>
      </div>
    </div>
  )
}
