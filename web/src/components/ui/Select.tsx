import { useEffect, useId, useRef, useState, type KeyboardEvent } from 'react'
import './Select.css'

/** Definicja opcji wyboru w komponencie Select. */
export interface SelectOption<T extends string = string> {
  /** Unikalna wartość opcji. */
  value: T
  /** Etykieta wyświetlana w menu rozwijanym. */
  label: string
  /** Opcjonalna wskazówka pomocnicza przy opcji. */
  hint?: string
}

/** Właściwości dla dostosowanego komponentu wyboru Select. */
export interface SelectProps<T extends string = string> {
  /** Aktualnie wybrana wartość. */
  value: T
  /** Callback przy zmianie wybranej opcji. */
  onChange: (value: T) => void
  /** Lista dostępnych opcji do wyboru. */
  options: SelectOption<T>[]
  /** Czy pole jest zablokowane. */
  disabled?: boolean
  /** Dodatkowa klasa CSS. */
  className?: string
  /** Identyfikator pola. */
  id?: string
  /** Tekst domyślny przy braku wyboru. */
  placeholder?: string
  /** Etykieta dostępności dla czytników ekranu. */
  ariaLabel?: string
}

/**
 * Komponent listy rozwijanej Select dostosowany stylizacyjnie i dostępny z klawiatury (WCAG strzałki/enter/home/end/esc).
 *
 * @example
 * <Select value={role} onChange={setRole} options={[{ value: 'PATIENT', label: 'Pacjent' }]} />
 */
export function Select<T extends string = string>({
  value,
  onChange,
  options,
  disabled = false,
  className = '',
  id,
  placeholder = 'Wybierz…',
  ariaLabel,
}: SelectProps<T>) {
  const [isOpen, setIsOpen] = useState(false)
  const [activeIndex, setActiveIndex] = useState(0)
  const containerRef = useRef<HTMLDivElement>(null)
  const triggerRef = useRef<HTMLButtonElement>(null)

  const generatedId = useId()
  const triggerId = id ?? `select-trigger-${generatedId}`
  const listboxId = `select-listbox-${generatedId}`

  const selectedOption = options.find((opt) => opt.value === value)
  const activeOption = options[activeIndex]
  const activeOptionId = isOpen && activeOption ? `${listboxId}-opt-${activeOption.value}` : undefined

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
    const idx = options.findIndex((opt) => opt.value === value)
    setActiveIndex(idx >= 0 ? idx : 0)
  }

  const handleSelectOption = (optValue: T) => {
    onChange(optValue)
    setIsOpen(false)
    triggerRef.current?.focus()
  }

  const handleKeyDown = (e: KeyboardEvent<HTMLButtonElement | HTMLDivElement>) => {
    if (disabled) return

    if (!isOpen) {
      if (['ArrowDown', 'ArrowUp', 'Enter', ' ', 'Home', 'End'].includes(e.key)) {
        e.preventDefault()
        setIsOpen(true)
        const idx = options.findIndex((opt) => opt.value === value)
        setActiveIndex(idx >= 0 ? idx : 0)
      }
      return
    }

    if (options.length === 0) {
      if (['Escape', 'Tab'].includes(e.key)) {
        setIsOpen(false)
        triggerRef.current?.focus()
      }
      return
    }

    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault()
        setActiveIndex((prev) => (prev + 1) % options.length)
        break
      case 'ArrowUp':
        e.preventDefault()
        setActiveIndex((prev) => (prev - 1 + options.length) % options.length)
        break
      case 'Home':
        e.preventDefault()
        setActiveIndex(0)
        break
      case 'End':
        e.preventDefault()
        setActiveIndex(options.length - 1)
        break
      case 'Enter':
      case ' ':
        e.preventDefault()
        if (options[activeIndex]) {
          handleSelectOption(options[activeIndex].value)
        }
        break
      case 'Escape':
        e.preventDefault()
        setIsOpen(false)
        triggerRef.current?.focus()
        break
      case 'Tab':
        setIsOpen(false)
        break
    }
  }

  return (
    <div
      ref={containerRef}
      className={`ui-select ${disabled ? 'ui-select--disabled' : ''} ${className}`.trim()}
    >
      <button
        ref={triggerRef}
        type="button"
        id={triggerId}
        className={`ui-select__trigger ${isOpen ? 'ui-select__trigger--active' : ''}`}
        onClick={handleToggle}
        onKeyDown={handleKeyDown}
        disabled={disabled}
        aria-haspopup="listbox"
        aria-expanded={isOpen}
        aria-controls={isOpen ? listboxId : undefined}
        aria-activedescendant={activeOptionId}
        aria-label={ariaLabel}
      >
        <span className="ui-select__value">
          {selectedOption ? (
            selectedOption.label
          ) : (
            <span className="ui-select__placeholder">{placeholder}</span>
          )}
        </span>
        <svg
          className={`ui-select__chevron ${isOpen ? 'ui-select__chevron--open' : ''}`}
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
          id={listboxId}
          className="ui-select__popover"
          role="listbox"
          tabIndex={-1}
          aria-label={ariaLabel}
        >
          {options.length === 0 ? (
            <div className="ui-select__option ui-select__option--empty" role="status">
              <span className="ui-select__option-label">Brak dostępnych opcji</span>
            </div>
          ) : (
            options.map((opt, idx) => {
              const isSelected = opt.value === value
              const isActive = idx === activeIndex
              const optionId = `${listboxId}-opt-${opt.value}`

              return (
                <div
                  key={opt.value}
                  id={optionId}
                  role="option"
                  aria-selected={isSelected}
                  className={`ui-select__option ${
                    isSelected ? 'ui-select__option--selected' : ''
                  } ${isActive ? 'ui-select__option--focused' : ''}`}
                  onClick={() => handleSelectOption(opt.value)}
                  onMouseEnter={() => setActiveIndex(idx)}
                >
                  <div className="ui-select__option-text">
                    <span className="ui-select__option-label">{opt.label}</span>
                    {opt.hint && <span className="ui-select__option-hint">{opt.hint}</span>}
                  </div>
                  {isSelected && (
                    <svg
                      className="ui-select__checkmark"
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
            })
          )}
        </div>
      )}
    </div>
  )
}
