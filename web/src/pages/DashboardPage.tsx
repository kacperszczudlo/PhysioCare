import { useCallback, useEffect, useMemo, useRef, useState, type CSSProperties } from 'react'
import { Link, useNavigate } from 'react-router-dom'

import { therapistApi } from '@/api/auth'
import { getErrorMessage } from '@/api/client'
import { exercisesApi } from '@/api/exercises'
import { schedulingApi } from '@/api/scheduling'
import type { DashboardStats, ExerciseCategory, Visit } from '@/api/types'
import { useAuth } from '@/auth/AuthContext'
import { EmptyState, ErrorBanner, LoadingBlock } from '@/components/AsyncState'
import { DashboardSkeleton } from '@/components/skeletons/WebSkeletons'
import { CreateExerciseModal } from '@/pages/exercises/CreateExerciseModal'
import { VisitFormModal } from '@/pages/schedule/VisitFormModal'
import { TherapistReviewsModal } from './dashboard/TherapistReviewsModal'
import { AuthMediaImg } from '@/components/AuthMedia'
import { addDays, formatTime, startOfDay, toDateInputValue } from '@/lib/scheduleTime'
import { isVisitRealtimeEvent } from '@/realtime/types'
import { useRealtimeEvents } from '@/realtime/useRealtimeEvents'
import './DashboardPage.css'

const UPCOMING_VISITS_PREVIEW = 5

/**
 * Generuje powitanie w zależności od pory dnia i imienia użytkownika.
 */
function greetingForHour(hour: number, firstName?: string): string {
  const name = firstName?.trim()
  const base = hour < 12 ? 'Dzień dobry' : hour < 18 ? 'Cześć' : 'Dobry wieczór'
  return name ? `${base}, ${name}` : base
}

function initials(first: string, last: string): string {
  return `${first.charAt(0)}${last.charAt(0)}`.toUpperCase() || '?'
}

function visitDurationMin(visit: Visit): number {
  const ms = new Date(visit.end_at).getTime() - new Date(visit.start_at).getTime()
  if (!Number.isFinite(ms) || ms <= 0) {
    return visit.therapy_type_duration_min || 0
  }
  return Math.round(ms / 60_000)
}

function formatVisitWhen(start: Date, today: Date): string {
  const time = formatTime(start)
  const visitDay = startOfDay(start)
  const todayStart = startOfDay(today)
  const tomorrowStart = startOfDay(addDays(todayStart, 1))

  if (visitDay.getTime() === todayStart.getTime()) {
    return `dziś ${time}`
  }
  if (visitDay.getTime() === tomorrowStart.getTime()) {
    return `jutro ${time}`
  }
  const dayLabel = new Intl.DateTimeFormat('pl-PL', {
    weekday: 'short',
    day: 'numeric',
    month: 'short',
  }).format(start)
  return `${dayLabel} ${time}`
}

function formatFullDate(date: Date): string {
  return new Intl.DateTimeFormat('pl-PL', {
    weekday: 'long',
    day: 'numeric',
    month: 'long',
    year: 'numeric',
  }).format(date)
}

function DateBadge({ now }: { now: Date }) {
  const weekday = new Intl.DateTimeFormat('pl-PL', { weekday: 'long' }).format(now)
  const day = new Intl.DateTimeFormat('pl-PL', { day: 'numeric' }).format(now)
  const monthYear = new Intl.DateTimeFormat('pl-PL', {
    month: 'long',
    year: 'numeric',
  }).format(now)

  return (
    <time className="dash-date" dateTime={toDateInputValue(now)} aria-label={formatFullDate(now)}>
      <span className="dash-date__weekday">{weekday}</span>
      <span className="dash-date__day">{day}</span>
      <span className="dash-date__month">{monthYear}</span>
    </time>
  )
}

function IconVisits() {
  return (
    <svg className="dash-metric__glyph" viewBox="0 0 48 48" aria-hidden="true">
      <rect x="8" y="10" width="32" height="30" rx="6" fill="currentColor" opacity="0.12" />
      <path
        d="M16 8v6M32 8v6M8 20h32"
        fill="none"
        stroke="currentColor"
        strokeWidth="2.2"
        strokeLinecap="round"
      />
      <circle cx="18" cy="28" r="2.2" fill="currentColor" />
      <circle cx="24" cy="28" r="2.2" fill="currentColor" />
      <circle cx="30" cy="28" r="2.2" fill="currentColor" />
      <circle cx="18" cy="34" r="2.2" fill="currentColor" opacity="0.45" />
      <circle cx="24" cy="34" r="2.2" fill="currentColor" opacity="0.45" />
    </svg>
  )
}

function IconPatients() {
  return (
    <svg className="dash-metric__glyph" viewBox="0 0 48 48" aria-hidden="true">
      <circle cx="18" cy="16" r="6" fill="currentColor" opacity="0.18" />
      <circle cx="30" cy="18" r="5" fill="currentColor" opacity="0.12" />
      <path d="M8 38c1.5-7 6-11 10-11s8.5 4 10 11" fill="currentColor" opacity="0.18" />
      <path d="M24 38c1-5.5 4.2-8.5 7.5-8.5S38 32 39 38" fill="currentColor" opacity="0.12" />
      <circle cx="18" cy="16" r="4.5" fill="none" stroke="currentColor" strokeWidth="2" />
      <circle cx="30" cy="18" r="3.5" fill="none" stroke="currentColor" strokeWidth="2" />
    </svg>
  )
}

function IconExercises() {
  return (
    <svg className="dash-metric__glyph" viewBox="0 0 48 48" aria-hidden="true">
      <path
        d="M14 30c4-8 8-12 16-14"
        fill="none"
        stroke="currentColor"
        strokeWidth="2.4"
        strokeLinecap="round"
      />
      <circle cx="12" cy="32" r="5" fill="currentColor" opacity="0.15" />
      <circle cx="36" cy="14" r="5" fill="currentColor" opacity="0.15" />
      <circle cx="12" cy="32" r="3.2" fill="none" stroke="currentColor" strokeWidth="2" />
      <circle cx="36" cy="14" r="3.2" fill="none" stroke="currentColor" strokeWidth="2" />
      <path
        d="M18 22l4 2 3-5 5 3"
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
        opacity="0.55"
      />
    </svg>
  )
}

function IconStar() {
  return (
    <svg className="dash-metric__glyph" viewBox="0 0 48 48" aria-hidden="true">
      <circle cx="24" cy="24" r="18" fill="currentColor" opacity="0.12" />
      <path
        d="M24 10l4.3 8.7 9.7 1.4-7 6.8 1.7 9.6-8.7-4.6-8.7 4.6 1.7-9.6-7-6.8 9.7-1.4L24 10z"
        fill="currentColor"
      />
    </svg>
  )
}

function polishReviewCount(count: number): string {
  if (count === 1) return 'opinia pacjenta'
  const mod10 = count % 10
  const mod100 = count % 100
  if (mod10 >= 2 && mod10 <= 4 && (mod100 < 10 || mod100 >= 20)) {
    return 'opinie pacjentów'
  }
  return 'opinii pacjentów'
}

function IconClock() {
  return (
    <svg className="dash-visit__ico" viewBox="0 0 20 20" aria-hidden="true">
      <circle cx="10" cy="10" r="7.25" fill="none" stroke="currentColor" strokeWidth="1.6" />
      <path
        d="M10 6.5V10l2.5 1.8"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.6"
        strokeLinecap="round"
      />
    </svg>
  )
}

function IconTimer() {
  return (
    <svg className="dash-visit__ico" viewBox="0 0 20 20" aria-hidden="true">
      <path
        d="M7 3.5h6M10 3.5v2M6.2 7.2a5.8 5.8 0 1 0 7.6 0"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.6"
        strokeLinecap="round"
      />
      <path d="M10 9.2v2.6" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
    </svg>
  )
}

export function DashboardPage() {
  const { user } = useAuth()
  const navigate = useNavigate()
  const [now] = useState(() => new Date())
  const [stats, setStats] = useState<DashboardStats | null>(null)
  const [visits, setVisits] = useState<Visit[]>([])
  const [categories, setCategories] = useState<ExerciseCategory[]>([])
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [reloadToken, setReloadToken] = useState(0)
  const [createExerciseOpen, setCreateExerciseOpen] = useState(false)
  const [createVisitOpen, setCreateVisitOpen] = useState(false)
  const [reviewsModalOpen, setReviewsModalOpen] = useState(false)
  const showLoadingRef = useRef(true)
  const softReloadTimer = useRef<ReturnType<typeof setTimeout> | null>(null)

  const today = useMemo(() => startOfDay(now), [now])
  const greeting = greetingForHour(now.getHours(), user?.first_name)

  const nextVisits = useMemo(() => {
    return visits
      .filter((visit) => visit.status === 'SCHEDULED')
      .sort((a, b) => new Date(a.start_at).getTime() - new Date(b.start_at).getTime())
      .slice(0, UPCOMING_VISITS_PREVIEW)
  }, [visits])

  const reload = useCallback(() => {
    showLoadingRef.current = true
    setReloadToken((value) => value + 1)
  }, [])

  const softReload = useCallback(() => {
    showLoadingRef.current = false
    setReloadToken((value) => value + 1)
  }, [])

  useRealtimeEvents(
    useCallback(
      (event) => {
        if (!isVisitRealtimeEvent(event)) {
          return
        }
        if (softReloadTimer.current != null) {
          clearTimeout(softReloadTimer.current)
        }
        softReloadTimer.current = setTimeout(() => {
          softReloadTimer.current = null
          softReload()
        }, 250)
      },
      [softReload],
    ),
  )

  useEffect(() => {
    return () => {
      if (softReloadTimer.current != null) {
        clearTimeout(softReloadTimer.current)
      }
    }
  }, [])

  useEffect(() => {
    let cancelled = false

    async function load() {
      if (showLoadingRef.current) {
        setLoading(true)
      }
      setError(null)
      try {
        const [statsData, visitsData] = await Promise.all([
          therapistApi.getDashboardStats(),
          schedulingApi.listUpcomingVisits(UPCOMING_VISITS_PREVIEW),
        ])
        if (!cancelled) {
          setStats(statsData)
          setVisits(visitsData)
        }
      } catch (err) {
        if (!cancelled) {
          setStats(null)
          setVisits([])
          setError(getErrorMessage(err, 'Nie udało się pobrać pulpitu.'))
        }
      } finally {
        if (!cancelled) {
          showLoadingRef.current = true
          setLoading(false)
        }
      }
    }

    void load()
    return () => {
      cancelled = true
    }
  }, [reloadToken])

  useEffect(() => {
    let cancelled = false
    async function loadCategories() {
      try {
        const data = await exercisesApi.listCategories()
        if (!cancelled) {
          setCategories(data)
        }
      } catch {
        if (!cancelled) {
          setCategories([])
        }
      }
    }
    void loadCategories()
    return () => {
      cancelled = true
    }
  }, [])

  return (
    <section className="dashboard">
      <header className="dash-hero">
        <div className="dash-hero__copy">
          <h1 className="dash-hero__title">{greeting}</h1>
          <p className="dash-hero__sub">
            Szybki przegląd dnia - wizyty, pacjenci i zalecenia w jednym miejscu.
          </p>
        </div>
        <DateBadge now={now} />
      </header>

      {loading ? (
        <LoadingBlock label="Ładowanie pulpitu…" skeleton={<DashboardSkeleton />} />
      ) : null}

      {error ? <ErrorBanner message={error} onRetry={reload} /> : null}

      {!loading && !error && stats ? (
        <>
          <div className="dash-metrics" role="list">
            <Link to="/schedule" className="dash-metric dash-metric--visits" role="listitem">
              <span className="dash-metric__icon" aria-hidden="true">
                <IconVisits />
              </span>
              <span className="dash-metric__body">
                <span className="dash-metric__value">{stats.visits_today}</span>
                <span className="dash-metric__label">Wizyty dziś</span>
                <span className="dash-metric__hint">
                  {stats.visits_today === 0
                    ? 'Wolny dzień w kalendarzu'
                    : stats.visits_today === 1
                      ? 'Jedna zaplanowana wizyta'
                      : `${stats.visits_today} zaplanowane wizyty`}
                </span>
              </span>
            </Link>

            <Link to="/patients" className="dash-metric dash-metric--patients" role="listitem">
              <span className="dash-metric__icon" aria-hidden="true">
                <IconPatients />
              </span>
              <span className="dash-metric__body">
                <span className="dash-metric__value">{stats.patients_total}</span>
                <span className="dash-metric__label">Pacjenci</span>
                <span className="dash-metric__hint">
                  {stats.patients_total === 0 ? 'Dodaj pierwszego pacjenta' : 'W Twojej opiece'}
                </span>
              </span>
            </Link>

            <Link to="/exercises" className="dash-metric dash-metric--exercises" role="listitem">
              <span className="dash-metric__icon" aria-hidden="true">
                <IconExercises />
              </span>
              <span className="dash-metric__body">
                <span className="dash-metric__value">{stats.assignments_active ?? 0}</span>
                <span className="dash-metric__label">Zalecane ćwiczenia</span>
                <span className="dash-metric__hint">
                  {(stats.assignments_active ?? 0) === 0
                    ? 'Brak aktywnych zaleceń'
                    : 'Aktywne przypisania'}
                </span>
              </span>
            </Link>

            <button
              type="button"
              className="dash-metric dash-metric--reviews"
              role="listitem"
              onClick={() => setReviewsModalOpen(true)}
              aria-label="Opinie i oceny pacjentów"
            >
              <span className="dash-metric__icon" aria-hidden="true">
                <IconStar />
              </span>
              <span className="dash-metric__body">
                <span className="dash-metric__value">
                  {stats.rating_count && stats.rating_count > 0
                    ? `★ ${Number(stats.rating_avg).toFixed(1)}`
                    : '—'}
                </span>
                <span className="dash-metric__label">Opinie pacjentów</span>
                <span className="dash-metric__hint">
                  {stats.rating_count && stats.rating_count > 0
                    ? `${stats.rating_count} ${polishReviewCount(stats.rating_count)}`
                    : 'Czeka na pierwsze opinie'}
                </span>
              </span>
            </button>
          </div>

          <div className="dash-split">
            <section className="dash-panel" aria-labelledby="dash-visits-heading">
              <div className="dash-panel__head">
                <div>
                  <h2 id="dash-visits-heading" className="dash-panel__title">
                    Najbliższe wizyty
                  </h2>
                  <p className="dash-panel__desc">
                    Kolejne zaplanowane terminy - dziś, jutro i dalej.
                  </p>
                </div>
                <Link className="dash-panel__link" to="/schedule">
                  Pełny harmonogram
                </Link>
              </div>

              {nextVisits.length === 0 ? (
                <EmptyState
                  title="Brak nadchodzących wizyt"
                  description="Zaplanuj termin w harmonogramie - pokażemy tu najbliższe."
                  action={
                    <button
                      type="button"
                      className="dash-empty-action"
                      onClick={() => setCreateVisitOpen(true)}
                    >
                      Zaplanuj wizytę
                    </button>
                  }
                />
              ) : (
                <ul className="dash-visits">
                  {nextVisits.map((visit) => {
                    const start = new Date(visit.start_at)
                    const duration = visitDurationMin(visit)
                    const name = `${visit.patient_first_name} ${visit.patient_last_name}`.trim()
                    return (
                      <li key={visit.id}>
                        <Link
                          className="dash-visit"
                          to="/schedule"
                          style={
                            {
                              '--visit-tint': visit.therapy_type_color || 'var(--color-primary)',
                            } as CSSProperties
                          }
                        >
                          {visit.patient_avatar_url ? (
                            <AuthMediaImg
                              path={visit.patient_avatar_url}
                              className="dash-visit__avatar"
                            />
                          ) : (
                            <span className="dash-visit__avatar" aria-hidden="true">
                              {initials(visit.patient_first_name, visit.patient_last_name)}
                            </span>
                          )}
                          <span className="dash-visit__main">
                            <span className="dash-visit__name">{name}</span>
                            <span className="dash-visit__type">{visit.therapy_type_name}</span>
                          </span>
                          <span className="dash-visit__meta">
                            <span className="dash-visit__chip">
                              <IconClock />
                              {formatVisitWhen(start, today)}
                            </span>
                            <span className="dash-visit__chip">
                              <IconTimer />
                              {duration} min
                            </span>
                          </span>
                        </Link>
                      </li>
                    )
                  })}
                </ul>
              )}
            </section>

            <section
              className="dash-panel dash-panel--actions"
              aria-labelledby="dash-actions-heading"
            >
              <div className="dash-panel__head">
                <div>
                  <h2 id="dash-actions-heading" className="dash-panel__title">
                    Szybkie akcje
                  </h2>
                  <p className="dash-panel__desc">Najczęstsze kroki bez zbędnego klikania.</p>
                </div>
              </div>

              <div className="dash-actions">
                <button
                  type="button"
                  className="dash-action dash-action--primary"
                  onClick={() => setCreateExerciseOpen(true)}
                >
                  <span className="dash-action__mark" aria-hidden="true">
                    <IconExercises />
                  </span>
                  <span className="dash-action__text">
                    <span className="dash-action__label">Nowe ćwiczenie</span>
                    <span className="dash-action__hint">Dodaj wideo lub PDF do bazy</span>
                  </span>
                </button>

                <button
                  type="button"
                  className="dash-action"
                  onClick={() => setCreateVisitOpen(true)}
                >
                  <span className="dash-action__mark" aria-hidden="true">
                    <IconClock />
                  </span>
                  <span className="dash-action__text">
                    <span className="dash-action__label">Nowa wizyta</span>
                    <span className="dash-action__hint">Zaplanuj termin na dziś</span>
                  </span>
                </button>

                <Link className="dash-action" to="/patients">
                  <span className="dash-action__mark" aria-hidden="true">
                    <IconPatients />
                  </span>
                  <span className="dash-action__text">
                    <span className="dash-action__label">Lista pacjentów</span>
                    <span className="dash-action__hint">Karty, epizody, zalecenia</span>
                  </span>
                </Link>

                <button
                  type="button"
                  className="dash-action"
                  onClick={() => setReviewsModalOpen(true)}
                >
                  <span className="dash-action__mark" aria-hidden="true">
                    <svg viewBox="0 0 24 24" width="18" height="18" fill="currentColor">
                      <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2" />
                    </svg>
                  </span>
                  <span className="dash-action__text">
                    <span className="dash-action__label">Opinie pacjentów</span>
                    <span className="dash-action__hint">Oceny, recenzje i odpowiedzi</span>
                  </span>
                </button>
              </div>
            </section>
          </div>
        </>
      ) : null}

      <CreateExerciseModal
        open={createExerciseOpen}
        categories={categories}
        onClose={() => setCreateExerciseOpen(false)}
        onSaved={() => {
          setCreateExerciseOpen(false)
          navigate('/exercises')
        }}
      />

      <VisitFormModal
        open={createVisitOpen}
        day={today}
        initialMinutes={60}
        onClose={() => setCreateVisitOpen(false)}
        onCreated={() => {
          setCreateVisitOpen(false)
          reload()
        }}
      />

      {user?.id ? (
        <TherapistReviewsModal
          open={reviewsModalOpen}
          therapistId={user.id}
          onClose={() => setReviewsModalOpen(false)}
          onReviewsUpdated={reload}
        />
      ) : null}
    </section>
  )
}
