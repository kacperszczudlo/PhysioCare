import { useState, useEffect } from 'react'
import { schedulingApi } from '@/api/scheduling'
import type { AvailabilitySlot } from '@/api/types'
import { getErrorMessage } from '@/api/client'
import { Button } from '@/components/ui/Button'
import './AvailabilityManagerModal.css'

interface AvailabilityManagerModalProps {
  isOpen: boolean
  onClose: () => void
  onSlotsChanged?: () => void
}

const DAY_NAMES = ['Poniedziałek', 'Wtorek', 'Środa', 'Czwartek', 'Piątek', 'Sobota', 'Niedziela']

export function AvailabilityManagerModal({
  isOpen,
  onClose,
  onSlotsChanged,
}: AvailabilityManagerModalProps) {
  const [slots, setSlots] = useState<AvailabilitySlot[]>([])
  const [loading, setLoading] = useState(false)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [tab, setTab] = useState<'RECURRING' | 'SPECIFIC'>('RECURRING')

  // Form state - Recurring
  const [dayOfWeek, setDayOfWeek] = useState(0)
  const [startTime, setStartTime] = useState('08:00')
  const [endTime, setEndTime] = useState('16:00')

  // Form state - Specific date
  const [dateIso, setDateIso] = useState('')
  const [specStartTime, setSpecStartTime] = useState('09:00')
  const [specEndTime, setSpecEndTime] = useState('17:00')

  useEffect(() => {
    if (isOpen) {
      void loadSlots()
    }
  }, [isOpen])

  async function loadSlots() {
    setLoading(true)
    setError(null)
    try {
      const data = await schedulingApi.listAvailabilities()
      setSlots(data)
    } catch (err) {
      setError(getErrorMessage(err, 'Nie udało się pobrać slotów dostępności.'))
    } finally {
      setLoading(false)
    }
  }

  async function handleAddSlot(e: React.FormEvent) {
    e.preventDefault()
    setBusy(true)
    setError(null)
    try {
      if (tab === 'RECURRING') {
        await schedulingApi.createAvailability({
          is_recurring: true,
          day_of_week: dayOfWeek,
          start_time: `${startTime}:00`,
          end_time: `${endTime}:00`,
          is_active: true,
        })
      } else {
        if (!dateIso) {
          setError('Wybierz datę dla jednorazowego slotu dostępności.')
          setBusy(false)
          return
        }
        const start_at = new Date(`${dateIso}T${specStartTime}:00`).toISOString()
        const end_at = new Date(`${dateIso}T${specEndTime}:00`).toISOString()
        await schedulingApi.createAvailability({
          is_recurring: false,
          start_at,
          end_at,
          is_active: true,
        })
      }
      await loadSlots()
      onSlotsChanged?.()
    } catch (err) {
      setError(getErrorMessage(err, 'Błąd dodawania slotu dostępności.'))
    } finally {
      setBusy(false)
    }
  }

  async function handleDelete(id: string) {
    setBusy(true)
    setError(null)
    try {
      await schedulingApi.deleteAvailability(id)
      await loadSlots()
      onSlotsChanged?.()
    } catch (err) {
      setError(getErrorMessage(err, 'Nie udało się usunąć slotu.'))
    } finally {
      setBusy(false)
    }
  }

  if (!isOpen) return null

  return (
    <div className="availability-modal-backdrop" onClick={onClose}>
      <div
        className="availability-modal-content"
        onClick={(e) => e.stopPropagation()}
        role="dialog"
        aria-labelledby="avail-modal-title"
      >
        <div className="availability-modal-header">
          <h2 id="avail-modal-title" className="availability-modal-title">
            Grafik Dostępności Fizjoterapeuty
          </h2>
          <button
            type="button"
            className="availability-modal-close"
            onClick={onClose}
            aria-label="Zamknij"
          >
            ✕
          </button>
        </div>

        {error && (
          <div className="availability-modal-error" role="alert">
            {error}
          </div>
        )}

        <div className="availability-tabs" role="tablist">
          <button
            type="button"
            role="tab"
            aria-selected={tab === 'RECURRING'}
            className={`availability-tab ${tab === 'RECURRING' ? 'active' : ''}`}
            onClick={() => setTab('RECURRING')}
          >
            Grafik Tygodniowy (Cykliczny)
          </button>
          <button
            type="button"
            role="tab"
            aria-selected={tab === 'SPECIFIC'}
            className={`availability-tab ${tab === 'SPECIFIC' ? 'active' : ''}`}
            onClick={() => setTab('SPECIFIC')}
          >
            Dodatkowy Termin (Jednorazowy)
          </button>
        </div>

        <form onSubmit={handleAddSlot} className="availability-form">
          {tab === 'RECURRING' ? (
            <div className="availability-form-grid">
              <div className="availability-form-field">
                <label htmlFor="avail-dow" className="availability-label">
                  Dzień tygodnia
                </label>
                <select
                  id="avail-dow"
                  className="availability-input"
                  value={dayOfWeek}
                  onChange={(e) => setDayOfWeek(Number(e.target.value))}
                >
                  {DAY_NAMES.map((name, idx) => (
                    <option key={idx} value={idx}>
                      {name}
                    </option>
                  ))}
                </select>
              </div>
              <div className="availability-form-field">
                <label htmlFor="avail-start-time" className="availability-label">
                  Od godziny
                </label>
                <input
                  id="avail-start-time"
                  type="time"
                  className="availability-input"
                  value={startTime}
                  onChange={(e) => setStartTime(e.target.value)}
                  required
                />
              </div>
              <div className="availability-form-field">
                <label htmlFor="avail-end-time" className="availability-label">
                  Do godziny
                </label>
                <input
                  id="avail-end-time"
                  type="time"
                  className="availability-input"
                  value={endTime}
                  onChange={(e) => setEndTime(e.target.value)}
                  required
                />
              </div>
            </div>
          ) : (
            <div className="availability-form-grid">
              <div className="availability-form-field">
                <label htmlFor="avail-date" className="availability-label">
                  Data
                </label>
                <input
                  id="avail-date"
                  type="date"
                  className="availability-input"
                  value={dateIso}
                  onChange={(e) => setDateIso(e.target.value)}
                  required
                />
              </div>
              <div className="availability-form-field">
                <label htmlFor="avail-spec-start" className="availability-label">
                  Od godziny
                </label>
                <input
                  id="avail-spec-start"
                  type="time"
                  className="availability-input"
                  value={specStartTime}
                  onChange={(e) => setSpecStartTime(e.target.value)}
                  required
                />
              </div>
              <div className="availability-form-field">
                <label htmlFor="avail-spec-end" className="availability-label">
                  Do godziny
                </label>
                <input
                  id="avail-spec-end"
                  type="time"
                  className="availability-input"
                  value={specEndTime}
                  onChange={(e) => setSpecEndTime(e.target.value)}
                  required
                />
              </div>
            </div>
          )}

          <div className="availability-form-actions">
            <Button type="submit" variant="primary" disabled={busy}>
              + Dodaj Slot Dostępności
            </Button>
          </div>
        </form>

        <div className="availability-list-section">
          <h3 className="availability-list-title">Zdefiniowane Terminy Pracy</h3>

          {loading ? (
            <p className="availability-empty">Ładowanie slotów...</p>
          ) : slots.length === 0 ? (
            <p className="availability-empty">
              Brak zdefiniowanych slotów dostępności. Wszyscy pacjenci mogą rezerwować wizyty bez
              ograniczeń grafikowych.
            </p>
          ) : (
            <ul className="availability-slots-list">
              {slots.map((slot) => (
                <li key={slot.id} className="availability-slot-item">
                  <div className="availability-slot-info">
                    {slot.is_recurring ? (
                      <>
                        <span className="availability-badge recurring">Cykliczny</span>
                        <strong>{DAY_NAMES[slot.day_of_week ?? 0]}</strong>{' '}
                        <span>
                          {slot.start_time?.slice(0, 5)} - {slot.end_time?.slice(0, 5)}
                        </span>
                      </>
                    ) : (
                      <>
                        <span className="availability-badge specific">Jednorazowy</span>
                        <strong>
                          {slot.start_at ? new Date(slot.start_at).toLocaleDateString('pl-PL') : ''}
                        </strong>{' '}
                        <span>
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
                        </span>
                      </>
                    )}
                  </div>
                  <button
                    type="button"
                    className="availability-delete-btn"
                    onClick={() => handleDelete(slot.id)}
                    disabled={busy}
                    aria-label="Usuń slot dostępności"
                  >
                    Usuń
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </div>
  )
}
