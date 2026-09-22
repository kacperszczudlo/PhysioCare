import { useState, useRef, useEffect } from 'react'
import './CustomTimePicker.css'

interface CustomTimePickerProps {
  value: string
  onChange: (time: string) => void
  ariaLabel?: string
}

const HOURS = Array.from({ length: 17 }, (_, i) => String(i + 6).padStart(2, '0'))
const MINUTES = ['00', '15', '30', '45']

/**
 * Komponent wyboru godziny wizyty z ułatwieniami dostępu i siatką minut w krokach 15-minutowych.
 */
export function CustomTimePicker({ value, onChange, ariaLabel }: CustomTimePickerProps) {
  const [open, setOpen] = useState(false)
  const containerRef = useRef<HTMLDivElement>(null)

  const [selectedHour, selectedMinute] = value ? value.split(':') : ['08', '00']

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setOpen(false)
      }
    }
    if (open) {
      document.addEventListener('mousedown', handleClickOutside)
    }
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [open])

  const handleHourSelect = (h: string) => {
    const next = `${h}:${selectedMinute || '00'}`
    onChange(next)
  }

  const handleMinuteSelect = (m: string) => {
    const next = `${selectedHour || '08'}:${m}`
    onChange(next)
  }

  return (
    <div className="custom-time-picker" ref={containerRef}>
      <button
        type="button"
        className={`custom-time-picker__trigger ${open ? 'is-open' : ''}`}
        onClick={() => setOpen(!open)}
        aria-label={ariaLabel || 'Wybierz godzinę'}
        aria-expanded={open}
      >
        <span className="custom-time-picker__value">{value || '08:00'}</span>
        <svg
          className="custom-time-picker__chevron"
          width="10"
          height="6"
          viewBox="0 0 10 6"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
          aria-hidden="true"
        >
          <path
            d="M1 1L5 5L9 1"
            stroke="currentColor"
            strokeWidth="1.5"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>
      </button>

      {open && (
        <div className="custom-time-picker__popover" role="dialog">
          <div className="custom-time-picker__grid">
            <div className="custom-time-picker__col">
              <span className="custom-time-picker__col-title">Godzina</span>
              <div className="custom-time-picker__list">
                {HOURS.map((h) => (
                  <button
                    key={h}
                    type="button"
                    className={`custom-time-picker__item ${selectedHour === h ? 'is-selected' : ''}`}
                    onClick={() => handleHourSelect(h)}
                  >
                    {h}
                  </button>
                ))}
              </div>
            </div>

            <div className="custom-time-picker__col">
              <span className="custom-time-picker__col-title">Minuta</span>
              <div className="custom-time-picker__list">
                {MINUTES.map((m) => (
                  <button
                    key={m}
                    type="button"
                    className={`custom-time-picker__item ${selectedMinute === m ? 'is-selected' : ''}`}
                    onClick={() => handleMinuteSelect(m)}
                  >
                    :{m}
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
