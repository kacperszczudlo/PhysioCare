import { useEffect, useRef, useState, type KeyboardEvent } from 'react'
import type { EpisodeStatus } from '@/api/types'
import { EPISODE_STATUS_LABELS } from '@/lib/bodyMap'
import './StatusSelect.css'

/** Właściwości komponentu wyboru statusu epizodu leczenia. */
export interface StatusSelectProps {
  /** Aktualnie wybrany status epizodu terapeutycznego. */
  value: EpisodeStatus
  /** Callback zmiany statusu. */
  onChange: (value: EpisodeStatus) => void
  /** Czy pole jest zablokowane. */
  disabled?: boolean
  /** Dodatkowa klasa CSS. */
  className?: string
  /** Identyfikator pola. */
  id?: string
}

interface StatusOptionMeta {
  value: EpisodeStatus
  label: string
  pillClass: string
}

/** Meta dane opcji statusów wraz z odpowiednimi klasami etykiet (Pills). */
export const STATUS_OPTIONS_META: StatusOptionMeta[] = [
  {
    value: 'IN_PROGRESS',
    label: EPISODE_STATUS_LABELS['IN_PROGRESS'],
    pillClass: 'status-pill--in-progress',
  },
  {
    value: 'COMPLETED_SUCCESS',
    label: EPISODE_STATUS_LABELS['COMPLETED_SUCCESS'],
    pillClass: 'status-pill--completed',
  },
  {
    value: 'REFERRED',
    label: EPISODE_STATUS_LABELS['REFERRED'],
    pillClass: 'status-pill--referred',
  },
  {
    value: 'INTERRUPTED',
    label: EPISODE_STATUS_LABELS['INTERRUPTED'],
    pillClass: 'status-pill--interrupted',
  },
]

/**
 * Komponent wyboru statusu epizodu leczenia z kolorowymi pigułkami wizualnymi (Pills).
 *
 * @example
 * <StatusSelect value={status} onChange={setStatus} />
 */
export function StatusSelect({
  value,
  onChange,
  disabled = false,
  className = '',
  id,
}: StatusSelectProps) {
  const [isOpen, setIsOpen] = useState(false)
  const [activeIndex, setActiveIndex] = useState(0)
  const containerRef = useRef<HTMLDivElement>(null)

  const selectedMeta =
    STATUS_OPTIONS_META.find((opt) => opt.value === value) ?? STATUS_OPTIONS_META[0]

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setIsOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const handleToggle = () => {
    if (disabled) return
    setIsOpen((prev) => !prev)
    const idx = STATUS_OPTIONS_META.findIndex((opt) => opt.value === value)
    setActiveIndex(idx >= 0 ? idx : 0)
  }

  const handleSelectOption = (optValue: EpisodeStatus) => {
    onChange(optValue)
    setIsOpen(false)
  }

  const handleKeyDown = (e: KeyboardEvent<HTMLButtonElement | HTMLDivElement>) => {
    if (disabled) return

    if (!isOpen) {
      if (['ArrowDown', 'ArrowUp', 'Enter', ' '].includes(e.key)) {
        e.preventDefault()
        setIsOpen(true)
        const idx = STATUS_OPTIONS_META.findIndex((opt) => opt.value === value)
        setActiveIndex(idx >= 0 ? idx : 0)
      }
      return
    }

    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault()
        setActiveIndex((prev) => (prev + 1) % STATUS_OPTIONS_META.length)
        break
      case 'ArrowUp':
        e.preventDefault()
        setActiveIndex(
          (prev) => (prev - 1 + STATUS_OPTIONS_META.length) % STATUS_OPTIONS_META.length,
        )
        break
      case 'Enter':
      case ' ':
        e.preventDefault()
        handleSelectOption(STATUS_OPTIONS_META[activeIndex].value)
        break
      case 'Escape':
      case 'Tab':
        setIsOpen(false)
        break
    }
  }

  return (
    <div
      ref={containerRef}
      className={`status-select ${disabled ? 'status-select--disabled' : ''} ${className}`.trim()}
    >
      <button
        type="button"
        id={id}
        className={`status-select__trigger ${isOpen ? 'status-select__trigger--active' : ''}`}
        onClick={handleToggle}
        onKeyDown={handleKeyDown}
        disabled={disabled}
        aria-haspopup="listbox"
        aria-expanded={isOpen}
        aria-label="Wybierz status epizodu"
      >
        <span className={`status-pill ${selectedMeta.pillClass}`}>
          <span>{selectedMeta.label}</span>
        </span>
        <svg
          className={`status-select__chevron ${isOpen ? 'status-select__chevron--open' : ''}`}
          width="16"
          height="16"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
          aria-hidden="true"
        >
          <polyline points="6 9 12 15 18 9" />
        </svg>
      </button>

      {isOpen && (
        <div
          className="status-select__popover"
          role="listbox"
          tabIndex={-1}
          aria-activedescendant={`status-option-${STATUS_OPTIONS_META[activeIndex].value}`}
        >
          {STATUS_OPTIONS_META.map((opt, idx) => {
            const isSelected = opt.value === value
            const isActive = idx === activeIndex

            return (
              <div
                key={opt.value}
                id={`status-option-${opt.value}`}
                role="option"
                aria-selected={isSelected}
                className={`status-select__option ${
                  isSelected ? 'status-select__option--selected' : ''
                } ${isActive ? 'status-select__option--focused' : ''}`}
                onClick={() => handleSelectOption(opt.value)}
                onMouseEnter={() => setActiveIndex(idx)}
              >
                <span className={`status-pill ${opt.pillClass}`}>
                  <span>{opt.label}</span>
                </span>
                {isSelected && (
                  <svg
                    className="status-select__checkmark"
                    width="16"
                    height="16"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2.5"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    aria-hidden="true"
                  >
                    <polyline points="20 6 9 17 4 12" />
                  </svg>
                )}
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
