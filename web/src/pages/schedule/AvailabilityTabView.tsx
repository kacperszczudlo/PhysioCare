import { useState, useEffect, useMemo } from 'react'
import { schedulingApi } from '@/api/scheduling'
import type { AvailabilitySlot, Holiday } from '@/api/types'
import { getErrorMessage } from '@/api/client'
import { Button } from '@/components/ui/Button'
import { AvailabilitySkeleton } from '@/components/skeletons/WebSkeletons'
import { CustomTimePicker } from '@/components/ui/CustomTimePicker'
import { DateCarousel } from '@/components/ui/DateCarousel'
import { useToast } from '@/components/ui/ToastContext'
import { toDateInputValue } from '@/lib/scheduleTime'
import './AvailabilityTabView.css'

const DAY_NAMES = ['Poniedziałek', 'Wtorek', 'Środa', 'Czwartek', 'Piątek', 'Sobota', 'Niedziela']

function getDurationLabel(startTime: string, endTime: string): string | null {
  const [h1, m1] = startTime.split(':').map(Number)
  const [h2, m2] = endTime.split(':').map(Number)
  if (isNaN(h1) || isNaN(m1) || isNaN(h2) || isNaN(m2)) return null
  const mins1 = h1 * 60 + m1
  const mins2 = h2 * 60 + m2
  const diff = mins2 - mins1
  if (diff <= 0) return null
  const hours = Math.floor(diff / 60)
  const mins = diff % 60
  if (mins === 0) return `${hours}h`
  return `${hours}h ${mins}m`
}

function PlusIcon() {
  return (
    <svg
      width="14"
      height="14"
      viewBox="0 0 14 14"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      aria-hidden="true"
    >
      <path d="M7 1V13M1 7H13" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
    </svg>
  )
}

function TrashIcon() {
  return (
    <svg
      width="14"
      height="14"
      viewBox="0 0 14 14"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      aria-hidden="true"
    >
      <path d="M1 1L13 13M1 13L13 1" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
    </svg>
  )
}

function PauseIcon() {
  return (
    <svg
      width="12"
      height="12"
      viewBox="0 0 12 12"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      aria-hidden="true"
    >
      <rect x="2" y="2" width="2.5" height="8" rx="1" fill="currentColor" />
      <rect x="7.5" y="2" width="2.5" height="8" rx="1" fill="currentColor" />
    </svg>
  )
}

interface DayConfig {
  enabled: boolean
  blocks: { startTime: string; endTime: string }[]
}

interface AvailabilityTabViewProps {
  onScheduleSaved?: () => void
}

/**
 * Widok zakładek konfiguracji dostępności gabinetu (grafik powtarzalny, jednorazowy i dni wolne).
 */
export function AvailabilityTabView({ onScheduleSaved }: AvailabilityTabViewProps = {}) {
  const { toast } = useToast()
  const [slots, setSlots] = useState<AvailabilitySlot[]>([])
  const [holidays, setHolidays] = useState<Holiday[]>([])
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const [weeklyConfig, setWeeklyConfig] = useState<Record<number, DayConfig>>(() => {
    const initial: Record<number, DayConfig> = {}
    for (let i = 0; i < 7; i++) {
      initial[i] = {
        enabled: i < 5,
        blocks: [{ startTime: '08:00', endTime: '16:00' }],
      }
    }
    return initial
  })

  const [hasSavedSchedule, setHasSavedSchedule] = useState<boolean | null>(null)
  const [savedWeeklyConfig, setSavedWeeklyConfig] = useState<Record<number, DayConfig> | null>(null)
  const [overrideDate, setOverrideDate] = useState<string>(() => toDateInputValue(new Date()))
  const [overrideStart, setOverrideStart] = useState('09:00')
  const [overrideEnd, setOverrideEnd] = useState('17:00')

  useEffect(() => {
    void loadData()
  }, [])

  async function loadData() {
    setLoading(true)
    setError(null)
    try {
      const [data, holidayList] = await Promise.all([
        schedulingApi.listAvailabilities(),
        schedulingApi.listPolishHolidays(new Date().getFullYear()),
      ])
      setSlots(data)
      setHolidays(holidayList)

      const recurring = data.filter((s) => s.is_recurring && s.is_active)
      const hasRecurring = recurring.length > 0
      setHasSavedSchedule(hasRecurring)

      if (hasRecurring) {
        const updated: Record<number, DayConfig> = {}
        for (let i = 0; i < 7; i++) {
          const daySlots = recurring.filter((s) => s.day_of_week === i)
          if (daySlots.length > 0) {
            updated[i] = {
              enabled: true,
              blocks: daySlots.map((s) => ({
                startTime: (s.start_time || '08:00').slice(0, 5),
                endTime: (s.end_time || '16:00').slice(0, 5),
              })),
            }
          } else {
            updated[i] = { enabled: false, blocks: [{ startTime: '08:00', endTime: '16:00' }] }
          }
        }
        setWeeklyConfig(updated)
        setSavedWeeklyConfig(updated)
      } else {
        setSavedWeeklyConfig(null)
      }
    } catch (err) {
      setError(getErrorMessage(err, 'Nie udało się pobrać grafiku dostępności.'))
    } finally {
      setLoading(false)
    }
  }

  const isDirty = useMemo(() => {
    if (!hasSavedSchedule) return true
    if (!savedWeeklyConfig) return false
    return JSON.stringify(weeklyConfig) !== JSON.stringify(savedWeeklyConfig)
  }, [hasSavedSchedule, savedWeeklyConfig, weeklyConfig])

  const applyDefaultTemplate = () => {
    const template: Record<number, DayConfig> = {}
    for (let i = 0; i < 7; i++) {
      template[i] = {
        enabled: i < 5,
        blocks: [{ startTime: '08:00', endTime: '16:00' }],
      }
    }
    setWeeklyConfig(template)
  }

  const clearAllDays = () => {
    const cleared: Record<number, DayConfig> = {}
    for (let i = 0; i < 7; i++) {
      cleared[i] = {
        enabled: false,
        blocks: [{ startTime: '08:00', endTime: '16:00' }],
      }
    }
    setWeeklyConfig(cleared)
  }

  const toggleDayEnabled = (dayIdx: number) => {
    setWeeklyConfig((prev) => ({
      ...prev,
      [dayIdx]: {
        ...prev[dayIdx],
        enabled: !prev[dayIdx].enabled,
      },
    }))
  }

  const addTimeBlock = (dayIdx: number) => {
    setWeeklyConfig((prev) => {
      const currentBlocks = prev[dayIdx].blocks
      const lastEnd =
        currentBlocks.length > 0 ? currentBlocks[currentBlocks.length - 1].endTime : '12:00'
      return {
        ...prev,
        [dayIdx]: {
          ...prev[dayIdx],
          blocks: [...currentBlocks, { startTime: lastEnd, endTime: '17:00' }],
        },
      }
    })
  }

  const removeTimeBlock = (dayIdx: number, blockIdx: number) => {
    setWeeklyConfig((prev) => ({
      ...prev,
      [dayIdx]: {
        ...prev[dayIdx],
        blocks: prev[dayIdx].blocks.filter((_, idx) => idx !== blockIdx),
      },
    }))
  }

  const updateTimeBlock = (
    dayIdx: number,
    blockIdx: number,
    field: 'startTime' | 'endTime',
    value: string,
  ) => {
    setWeeklyConfig((prev) => {
      const updatedBlocks = [...prev[dayIdx].blocks]
      updatedBlocks[blockIdx] = {
        ...updatedBlocks[blockIdx],
        [field]: value,
      }
      return {
        ...prev,
        [dayIdx]: {
          ...prev[dayIdx],
          blocks: updatedBlocks,
        },
      }
    })
  }

  async function handleSaveWeeklySchedule() {
    setSaving(true)
    setError(null)
    try {
      // 1. Delete existing recurring slots
      const existingRecurring = slots.filter((s) => s.is_recurring)
      for (const slot of existingRecurring) {
        await schedulingApi.deleteAvailability(slot.id)
      }

      // 2. Create new recurring slots from weeklyConfig
      for (let i = 0; i < 7; i++) {
        const cfg = weeklyConfig[i]
        if (cfg.enabled) {
          for (const block of cfg.blocks) {
            await schedulingApi.createAvailability({
              is_recurring: true,
              day_of_week: i,
              start_time: `${block.startTime}:00`,
              end_time: `${block.endTime}:00`,
              is_active: true,
            })
          }
        }
      }

      const wasPreviouslySaved = hasSavedSchedule
      await loadData()
      toast.success(
        wasPreviouslySaved
          ? 'Tygodniowy grafik pracy został pomyślnie zaktualizowany.'
          : 'Tygodniowy grafik pracy został pomyślnie zapisany i aktywowany!',
      )
      onScheduleSaved?.()
    } catch (err) {
      const errMsg = getErrorMessage(err, 'Błąd podczas zapisywania tygodniowego grafiku.')
      setError(errMsg)
      toast.error(errMsg)
    } finally {
      setSaving(false)
    }
  }

  async function handleAddOverride(e: React.FormEvent) {
    e.preventDefault()
    if (!overrideDate) {
      setError('Wybierz datę dyżuru.')
      return
    }
    setSaving(true)
    setError(null)
    try {
      const start_at = new Date(`${overrideDate}T${overrideStart}:00`).toISOString()
      const end_at = new Date(`${overrideDate}T${overrideEnd}:00`).toISOString()
      await schedulingApi.createAvailability({
        is_recurring: false,
        start_at,
        end_at,
        is_active: true,
      })
      await loadData()
      toast.success('Dodano dodatkowy termin pracy.')
    } catch (err) {
      const errMsg = getErrorMessage(err, 'Błąd dodawania wyjątku.')
      setError(errMsg)
      toast.error(errMsg)
    } finally {
      setSaving(false)
    }
  }

  async function handleDeleteSlot(id: string) {
    setSaving(true)
    setError(null)
    try {
      await schedulingApi.deleteAvailability(id)
      await loadData()
      toast.success('Usunięto termin pracy.')
    } catch (err) {
      const errMsg = getErrorMessage(err, 'Nie udało się usunąć slotu.')
      setError(errMsg)
      toast.error(errMsg)
    } finally {
      setSaving(false)
    }
  }

  const specificSlots = slots.filter((s) => !s.is_recurring)

  if (loading) {
    return <AvailabilitySkeleton />
  }

  return (
    <div className="avail-tab-container">
      {error && (
        <div className="avail-alert error" role="alert">
          {error}
        </div>
      )}

      {/* Main Grid Layout */}
      <div className="avail-main-grid">
        {/* Left Column: Weekly Schedule Matrix */}
        <section className="avail-card avail-weekly-card">
          <div className="avail-card-header">
            <div>
              <div className="avail-title-row">
                <h2 className="avail-card-title">Tygodniowy grafik pracy</h2>
                {hasSavedSchedule !== null && (
                  <span
                    className={`avail-status-pill ${
                      !hasSavedSchedule
                        ? 'is-unconfigured'
                        : isDirty
                          ? 'is-dirty'
                          : 'is-active'
                    }`}
                    role="status"
                  >
                    <span className="avail-status-dot" aria-hidden="true" />
                    {!hasSavedSchedule
                      ? 'Wymaga ustalenia i zapisu'
                      : isDirty
                        ? 'Niezapisane zmiany'
                        : 'Grafik aktywny'}
                  </span>
                )}
              </div>
              <p className="avail-card-subtitle">
                Zdefiniuj stałe godziny przyjęć pacjentów w poszczególnych dniach tygodnia.
              </p>
            </div>
            <div className="avail-card-actions">
              <Button
                type="button"
                variant={hasSavedSchedule && !isDirty ? 'secondary' : 'primary'}
                size="sm"
                onClick={handleSaveWeeklySchedule}
                disabled={saving || (hasSavedSchedule === true && !isDirty)}
              >
                {saving
                  ? 'Zapisywanie...'
                  : !hasSavedSchedule
                    ? 'Zapisz i aktywuj grafik'
                    : isDirty
                      ? 'Zapisz zmiany'
                      : 'Zapisano'}
              </Button>
            </div>
          </div>

          {hasSavedSchedule === false && (
            <div className="avail-unconfigured-banner" role="status">
              <div className="avail-unconfigured-banner__icon" aria-hidden="true">
                <svg
                  width="18"
                  height="18"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                >
                  <circle cx="12" cy="12" r="10" />
                  <line x1="12" y1="16" x2="12" y2="12" />
                  <line x1="12" y1="8" x2="12.01" y2="8" />
                </svg>
              </div>
              <div className="avail-unconfigured-banner__copy">
                <p className="avail-unconfigured-banner__title">
                  Harmonogram pracy nie został jeszcze zapisany
                </p>
                <p className="avail-unconfigured-banner__desc">
                  Poniższy rozkład to sugerowany wzorzec godzin (Pn–Pt 08:00–16:00). Dopasuj godziny
                  przyjęć do swojego gabinetu i kliknij <strong>„Zapisz i aktywuj grafik”</strong>,
                  aby pacjenci mogli rezerwować wizyty.
                </p>
              </div>
            </div>
          )}

          <div className="avail-preset-bar">
            <span className="avail-preset-label">Szybki szablon:</span>
            <button
              type="button"
              className="avail-preset-btn"
              onClick={applyDefaultTemplate}
              title="Włącz Pn–Pt 08:00–16:00"
            >
              Pn–Pt 08:00–16:00
            </button>
            <button
              type="button"
              className="avail-preset-btn"
              onClick={clearAllDays}
              title="Wyłącz wszystkie dni"
            >
              Wyczyść dni
            </button>
          </div>

          <div className="avail-weekly-rows">
            {DAY_NAMES.map((dayName, dayIdx) => {
              const cfg = weeklyConfig[dayIdx]
              return (
                <div
                  key={dayIdx}
                  className={`avail-day-row ${cfg.enabled ? 'is-enabled' : 'is-disabled'}`}
                >
                  <div className="avail-day-info">
                    <label className="avail-toggle-switch">
                      <input
                        type="checkbox"
                        checked={cfg.enabled}
                        onChange={() => toggleDayEnabled(dayIdx)}
                      />
                      <span className="avail-toggle-slider"></span>
                    </label>
                    <span className="avail-day-name">{dayName}</span>
                  </div>

                  <div className="avail-day-content">
                    {cfg.enabled ? (
                      <div className="avail-blocks-container">
                        {cfg.blocks.map((block, blockIdx) => {
                          const prevBlock = blockIdx > 0 ? cfg.blocks[blockIdx - 1] : null
                          const isBreak = prevBlock && prevBlock.endTime < block.startTime

                          return (
                            <div key={blockIdx} className="avail-block-inline-group">
                              {isBreak && (
                                <div
                                  className="avail-break-chip"
                                  title="Przerwa w przyjmowaniu pacjentów"
                                >
                                  <PauseIcon />
                                  <span>
                                    Przerwa {prevBlock.endTime} – {block.startTime}
                                  </span>
                                </div>
                              )}
                              <div className="avail-block-item">
                                <CustomTimePicker
                                  value={block.startTime}
                                  onChange={(next) =>
                                    updateTimeBlock(dayIdx, blockIdx, 'startTime', next)
                                  }
                                  ariaLabel="Czas rozpoczęcia bloku pracy"
                                />
                                <span className="avail-time-sep">–</span>
                                <CustomTimePicker
                                  value={block.endTime}
                                  onChange={(next) =>
                                    updateTimeBlock(dayIdx, blockIdx, 'endTime', next)
                                  }
                                  ariaLabel="Czas zakończenia bloku pracy"
                                />
                                {getDurationLabel(block.startTime, block.endTime) && (
                                  <span
                                    className="avail-block-duration"
                                    title="Czas trwania bloku pracy"
                                  >
                                    {getDurationLabel(block.startTime, block.endTime)}
                                  </span>
                                )}
                                {cfg.blocks.length > 1 && (
                                  <button
                                    type="button"
                                    className="avail-remove-block-btn"
                                    onClick={() => removeTimeBlock(dayIdx, blockIdx)}
                                    title="Usuń ten przedział godzin"
                                    aria-label="Usuń ten przedział godzin"
                                  >
                                    <TrashIcon />
                                  </button>
                                )}
                              </div>
                            </div>
                          )
                        })}
                        <button
                          type="button"
                          className="avail-add-block-btn"
                          onClick={() => addTimeBlock(dayIdx)}
                          title="Dodaj kolejny przedział godzin pracy w tym dniu"
                        >
                          <PlusIcon />
                          <span>Dodaj blok pracy</span>
                        </button>
                      </div>
                    ) : (
                      <span className="avail-day-off-label">Dzień niepracujący</span>
                    )}
                  </div>
                </div>
              )
            })}
          </div>
        </section>

        {/* Right Column: Specific Date Overrides & Vacation */}
        <aside className="avail-side-column">
          <section className="avail-card">
            <h2 className="avail-card-title">Dodatkowy Termin / Wyjątek</h2>
            <p className="avail-card-subtitle">
              Dodaj jednorazowy slot dyżuru poza stałym tygodniowym grafikiem.
            </p>

            <form onSubmit={handleAddOverride} className="avail-override-form">
              <DateCarousel
                label="Data dyżuru"
                value={overrideDate}
                onChange={setOverrideDate}
                minimumDate={toDateInputValue(new Date())}
                dayCount={90}
              />

              <div className="avail-field">
                <label className="avail-label">Godziny dyżuru</label>
                <div className="avail-range-picker-row">
                  <CustomTimePicker
                    value={overrideStart}
                    onChange={setOverrideStart}
                    ariaLabel="Godzina rozpoczęcia dyżuru"
                  />
                  <span className="avail-range-arrow">→</span>
                  <CustomTimePicker
                    value={overrideEnd}
                    onChange={setOverrideEnd}
                    ariaLabel="Godzina zakończenia dyżuru"
                  />
                  {getDurationLabel(overrideStart, overrideEnd) && (
                    <span className="avail-duration-chip" title="Czas trwania dyżuru">
                      {getDurationLabel(overrideStart, overrideEnd)}
                    </span>
                  )}
                </div>
              </div>

              <Button type="submit" variant="secondary" disabled={saving}>
                Dodaj wyjątek
              </Button>
            </form>
          </section>

          <section className="avail-card">
            <h2 className="avail-card-title">Aktywne Wyjątki Datowe</h2>
            {specificSlots.length === 0 ? (
              <p className="avail-empty-hint">Brak zdefiniowanych jednorazowych terminów.</p>
            ) : (
              <ul className="avail-overrides-list">
                {specificSlots.map((slot) => (
                  <li key={slot.id} className="avail-override-item">
                    <div>
                      <strong>
                        {slot.start_at ? new Date(slot.start_at).toLocaleDateString('pl-PL') : ''}
                      </strong>
                      <div className="avail-override-time">
                        {slot.start_at
                          ? new Date(slot.start_at).toLocaleTimeString('pl-PL', {
                              hour: '2-digit',
                              minute: '2-digit',
                            })
                          : ''}{' '}
                        -{' '}
                        {slot.end_at
                          ? new Date(slot.end_at).toLocaleTimeString('pl-PL', {
                              hour: '2-digit',
                              minute: '2-digit',
                            })
                          : ''}
                      </div>
                    </div>
                    <button
                      type="button"
                      className="avail-delete-icon-btn"
                      onClick={() => handleDeleteSlot(slot.id)}
                      disabled={saving}
                      title="Usuń ten wyjątek"
                    >
                      Usuń
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </section>

          <section className="avail-card">
            <h2 className="avail-card-title">Święta Ustawowe ({new Date().getFullYear()})</h2>
            <p className="avail-card-subtitle">
              Dni wolne od pracy – automatycznie wyłączają przyjmowanie z grafiku cyklicznego.
            </p>
            <div className="avail-holidays-list">
              {holidays.map((h) => (
                <div key={h.date} className="avail-holiday-item">
                  <div className="avail-holiday-info">
                    <span className="avail-holiday-name">{h.name}</span>
                    <span className="avail-holiday-date">
                      {new Date(h.date + 'T00:00:00').toLocaleDateString('pl-PL', {
                        weekday: 'short',
                        day: 'numeric',
                        month: 'long',
                      })}
                    </span>
                  </div>
                  <button
                    type="button"
                    className="avail-holiday-btn"
                    onClick={() => {
                      setOverrideDate(h.date)
                      window.scrollTo({ top: 300, behavior: 'smooth' })
                    }}
                    title="Skonfiguruj dyżur w to święto"
                  >
                    Ustal dyżur
                  </button>
                </div>
              ))}
            </div>
          </section>
        </aside>
      </div>
    </div>
  )
}
