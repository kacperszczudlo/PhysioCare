import React, { useEffect, useRef, useState } from 'react'
import L from 'leaflet'
import {
  DEFAULT_CENTER,
  reverseGeocode,
  searchAddress,
  type LocationAddressResult,
} from './locationServices'
import { useToast } from '@/components/ui/ToastContext'
import { Modal } from '@/components/ui/Modal'
import './LocationPickerModal.css'

interface LocationPickerModalProps {
  isOpen: boolean
  onClose: () => void
  onSelectLocation: (address: string, coords?: { lat: number; lon: number }) => void
  initialAddress?: string
}

const PIN_SVG = `<svg width="32" height="42" viewBox="0 0 32 42" fill="none" xmlns="http://www.w3.org/2000/svg">
  <path d="M16 0C7.16344 0 0 7.16344 0 16C0 27.2 14.2 40.7 15.35 41.78C15.72 42.13 16.28 42.13 16.65 41.78C17.8 40.7 32 27.2 32 16C32 7.16344 24.8366 0 16 0ZM16 22C12.6863 22 10 19.3137 10 16C10 12.6863 12.6863 10 16 10C19.3137 10 22 12.6863 22 16C22 19.3137 19.3137 22 16 22Z" fill="#2563eb"/>
</svg>`

const createCustomPinIcon = () =>
  L.divIcon({
    className: 'custom-map-pin',
    html: PIN_SVG,
    iconSize: [32, 42],
    iconAnchor: [16, 42],
  })

/**
 * Modal z interaktywnym wybierakiem lokalizacji geograficznej (geokodowanie odwrotne, przeciąganie pinezki).
 */
export const LocationPickerModal: React.FC<LocationPickerModalProps> = ({
  isOpen,
  onClose,
  onSelectLocation,
  initialAddress = '',
}) => {
  const mapContainerRef = useRef<HTMLDivElement | null>(null)
  const mapRef = useRef<L.Map | null>(null)
  const markerRef = useRef<L.Marker | null>(null)

  const [searchQuery, setSearchQuery] = useState('')
  const [suggestions, setSuggestions] = useState<LocationAddressResult[]>([])
  const [isSearching, setIsSearching] = useState(false)
  const [selectedAddress, setSelectedAddress] = useState(initialAddress)
  const [selectedCoords, setSelectedCoords] = useState<{ lat: number; lon: number }>({
    lat: DEFAULT_CENTER.lat,
    lon: DEFAULT_CENTER.lon,
  })
  const [isGpsLoading, setIsGpsLoading] = useState(false)

  useEffect(() => {
    if (isOpen) {
      setSelectedAddress(initialAddress)
      setSearchQuery('')
      setSuggestions([])
      if (initialAddress.trim().length > 3) {
        searchAddress(initialAddress).then((results) => {
          if (results.length > 0) {
            const first = results[0]
            setSelectedCoords({ lat: first.lat, lon: first.lon })
          }
        })
      }
    }
  }, [isOpen, initialAddress])

  useEffect(() => {
    if (!isOpen || !mapContainerRef.current) return

    if (!mapRef.current) {
      const map = L.map(mapContainerRef.current, {
        center: [selectedCoords.lat, selectedCoords.lon],
        zoom: 15,
        zoomControl: true,
      })

      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 19,
        attribution: '&copy; OpenStreetMap contributors',
      }).addTo(map)

      const marker = L.marker([selectedCoords.lat, selectedCoords.lon], {
        draggable: true,
        icon: createCustomPinIcon(),
      }).addTo(map)

      map.on('click', async (e: L.LeafletMouseEvent) => {
        const { lat, lng } = e.latlng
        marker.setLatLng([lat, lng])
        setSelectedCoords({ lat, lon: lng })

        const res = await reverseGeocode(lat, lng)
        if (res?.formatted_address) {
          setSelectedAddress(res.formatted_address)
        }
      })

      marker.on('dragend', async () => {
        const position = marker.getLatLng()
        setSelectedCoords({ lat: position.lat, lon: position.lng })

        const res = await reverseGeocode(position.lat, position.lng)
        if (res?.formatted_address) {
          setSelectedAddress(res.formatted_address)
        }
      })

      mapRef.current = map
      markerRef.current = marker
    } else {
      mapRef.current.setView([selectedCoords.lat, selectedCoords.lon], 15)
      if (markerRef.current) {
        markerRef.current.setLatLng([selectedCoords.lat, selectedCoords.lon])
      }
      setTimeout(() => {
        mapRef.current?.invalidateSize()
      }, 100)
    }

    return () => {
      if (mapRef.current) {
        mapRef.current.remove()
        mapRef.current = null
        markerRef.current = null
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isOpen])

  useEffect(() => {
    if (mapRef.current && markerRef.current && isOpen) {
      mapRef.current.setView([selectedCoords.lat, selectedCoords.lon], 15)
      markerRef.current.setLatLng([selectedCoords.lat, selectedCoords.lon])
    }
  }, [selectedCoords, isOpen])

  useEffect(() => {
    if (!searchQuery.trim() || searchQuery.trim().length < 3) {
      setSuggestions([])
      return
    }

    const abortController = new AbortController()
    setIsSearching(true)

    const timer = setTimeout(async () => {
      const results = await searchAddress(searchQuery, abortController.signal)
      setSuggestions(results)
      setIsSearching(false)
    }, 350)

    return () => {
      clearTimeout(timer)
      abortController.abort()
    }
  }, [searchQuery])

  const handleSelectSuggestion = (item: LocationAddressResult) => {
    setSelectedAddress(item.formatted_address)
    setSelectedCoords({ lat: item.lat, lon: item.lon })
    setSuggestions([])
    setSearchQuery('')
  }

  const { toast } = useToast()

  const handleUseGps = () => {
    if (!navigator.geolocation) {
      toast.error('Geolokalizacja nie jest wspierana przez Twoją przeglądarkę.')
      return
    }

    setIsGpsLoading(true)
    navigator.geolocation.getCurrentPosition(
      async (pos) => {
        const { latitude, longitude } = pos.coords
        setSelectedCoords({ lat: latitude, lon: longitude })
        setIsGpsLoading(false)

        const res = await reverseGeocode(latitude, longitude)
        if (res?.formatted_address) {
          setSelectedAddress(res.formatted_address)
        }
      },
      (err) => {
        setIsGpsLoading(false)
        console.warn('GPS location error:', err)
        toast.error('Nie udało się pobrać Twojej aktualnej pozycji GPS.')
      },
      { timeout: 10000, enableHighAccuracy: true },
    )
  }

  const handleConfirm = () => {
    onSelectLocation(
      selectedAddress || `${selectedCoords.lat.toFixed(5)}, ${selectedCoords.lon.toFixed(5)}`,
      selectedCoords,
    )
    onClose()
  }

  return (
    <Modal
      open={isOpen}
      title="Wybierz lokalizację z mapy"
      description="Wyszukaj adres lub kliknij bezpośrednio na mapie, aby ustawić pinezkę"
      size="xl"
      onClose={onClose}
      bodyClassName="location-picker-modal-body"
    >
      <div className="location-picker-search-bar">
        <div className="location-search-input-wrapper">
          <svg
            className="location-search-icon"
            width="16"
            height="16"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
          >
            <circle cx="11" cy="11" r="8"></circle>
            <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
          </svg>
          <input
            type="text"
            className="location-search-input"
            placeholder="Wpisz ulicę, miasto lub kod pocztowy..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
          {isSearching && (
            <div className="location-suggestions-dropdown">
              <div className="location-suggestion-item" style={{ color: 'var(--color-muted)' }}>
                Szukanie adresu…
              </div>
            </div>
          )}
          {!isSearching && suggestions.length > 0 && (
            <div className="location-suggestions-dropdown">
              {suggestions.map((item) => (
                <div
                  key={item.place_id}
                  className="location-suggestion-item"
                  onClick={() => handleSelectSuggestion(item)}
                >
                  <span className="location-suggestion-main">
                    {item.formatted_address || item.display_name}
                  </span>
                  <span className="location-suggestion-sub">{item.display_name}</span>
                </div>
              ))}
            </div>
          )}
        </div>

        <button
          type="button"
          className="location-gps-btn"
          onClick={handleUseGps}
          disabled={isGpsLoading}
        >
          <svg
            width="16"
            height="16"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
          >
            <circle cx="12" cy="12" r="10"></circle>
            <line x1="12" y1="2" x2="12" y2="6"></line>
            <line x1="12" y1="18" x2="12" y2="22"></line>
            <line x1="4.93" y1="4.93" x2="7.76" y2="7.76"></line>
            <line x1="16.24" y1="16.24" x2="19.07" y2="19.07"></line>
            <line x1="2" y1="12" x2="6" y2="12"></line>
            <line x1="18" y1="12" x2="22" y2="12"></line>
          </svg>
          {isGpsLoading ? 'Pobieranie...' : 'GPS'}
        </button>
      </div>

      <div className="location-picker-map-container">
        <div ref={mapContainerRef} className="location-picker-map-element" />
        <div className="location-hint-badge">
          Kliknij na mapie lub przeciągnij pinezkę, aby precyzyjnie ustalić adres
        </div>
      </div>

      <footer className="location-picker-footer">
        <div className="location-selected-address-preview">
          <span className="location-selected-badge">Wybrany adres:</span>
          <span>{selectedAddress || 'Brak wybranego adresu (kliknij na mapie)'}</span>
        </div>

        <div className="location-picker-actions">
          <button type="button" className="location-picker-cancel-btn" onClick={onClose}>
            Anuluj
          </button>
          <button
            type="button"
            className="location-picker-confirm-btn"
            onClick={handleConfirm}
            disabled={!selectedAddress.trim()}
          >
            Zatwierdź lokalizację
          </button>
        </div>
      </footer>
    </Modal>
  )
}
