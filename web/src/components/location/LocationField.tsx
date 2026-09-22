import React, { useEffect, useRef, useState } from 'react'
import { LocationPickerModal } from './LocationPickerModal'
import { searchAddress, type LocationAddressResult } from './locationServices'
import './LocationField.css'

/** Właściwości komponentu wyboru lokalizacji gabinetu. */
export interface LocationFieldProps {
  /** Etykieta formularza. */
  label?: string
  /** Nazwa atrybutu name dla pola input. */
  name?: string
  /** Aktualny opisowy adres lub lokalizacja. */
  value: string
  /** Callback wywoływany przy zmianie tekstu adresu lub wyborze z mapy. */
  onChange: (value: string) => void
  /** Tekst zastępczy (placeholder). */
  placeholder?: string
  /** Wskazówka pomocnicza umieszczona pod polem formularza. */
  hint?: string
  /** Komunikat błędu walidacji. */
  error?: string
  /** Czy pole jest wymagane. */
  required?: boolean
  /** Dodatkowa klasa CSS. */
  className?: string
}

/**
 * Komponent wyboru lokalizacji z automatycznym podpowiadaniem adresów oraz opcją otwarcia mapy.
 *
 * @example
 * <LocationField label="Adres gabinetu" value={address} onChange={setAddress} />
 */
export const LocationField: React.FC<LocationFieldProps> = ({
  label = 'Adres / lokalizacja gabinetu',
  name = 'location_address',
  value,
  onChange,
  placeholder = 'np. ul. Kwiatowa 12, 00-001 Warszawa',
  hint = 'Wpisz adres lub kliknij "Wybierz z mapy", aby ustalić położenie na interaktywnej mapie.',
  error,
  required = false,
  className = '',
}) => {
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [suggestions, setSuggestions] = useState<LocationAddressResult[]>([])
  const [showDropdown, setShowDropdown] = useState(false)
  const wrapperRef = useRef<HTMLDivElement | null>(null)

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (wrapperRef.current && !wrapperRef.current.contains(event.target as Node)) {
        setShowDropdown(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => {
      document.removeEventListener('mousedown', handleClickOutside)
    }
  }, [])

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newValue = e.target.value
    onChange(newValue)

    if (newValue.trim().length >= 3) {
      searchAddress(newValue).then((results) => {
        setSuggestions(results)
        setShowDropdown(results.length > 0)
      })
    } else {
      setSuggestions([])
      setShowDropdown(false)
    }
  }

  const handleSelectSuggestion = (item: LocationAddressResult) => {
    onChange(item.formatted_address)
    setShowDropdown(false)
  }

  return (
    <div className={`location-field-group ${className}`} ref={wrapperRef}>
      {label && (
        <label className="location-field-label" htmlFor={name}>
          {label} {required && <span style={{ color: '#ef4444' }}>*</span>}
        </label>
      )}

      <div className="location-field-controls">
        <div className="location-field-input-wrapper">
          <input
            id={name}
            name={name}
            type="text"
            className={`location-field-input ${error ? 'location-field-input--error' : ''}`}
            placeholder={placeholder}
            value={value}
            onChange={handleInputChange}
            onFocus={() => {
              if (suggestions.length > 0) setShowDropdown(true)
            }}
          />

          {showDropdown && suggestions.length > 0 && (
            <div className="location-field-inline-dropdown">
              {suggestions.map((item) => (
                <div
                  key={item.place_id}
                  className="location-field-inline-item"
                  onClick={() => handleSelectSuggestion(item)}
                >
                  {item.formatted_address || item.display_name}
                </div>
              ))}
            </div>
          )}
        </div>

        <button
          type="button"
          className="location-field-map-btn"
          onClick={() => setIsModalOpen(true)}
          title="Otwórz interaktywną mapę"
        >
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
            <polygon points="1 6 1 22 8 18 16 22 23 18 23 2 16 6 8 2 1 6"></polygon>
            <line x1="8" y1="2" x2="8" y2="18"></line>
            <line x1="16" y1="6" x2="16" y2="22"></line>
          </svg>
          Wybierz z mapy
        </button>
      </div>

      {error ? (
        <span className="location-field-error">{error}</span>
      ) : hint ? (
        <span className="location-field-hint">{hint}</span>
      ) : null}

      <LocationPickerModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        initialAddress={value}
        onSelectLocation={(selectedAddress) => {
          onChange(selectedAddress)
        }}
      />
    </div>
  )
}
