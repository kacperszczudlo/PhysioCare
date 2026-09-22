import React, { useEffect, useRef, useState } from 'react'
import L from 'leaflet'
import { DEFAULT_CENTER, openInGoogleMaps, searchAddress } from './locationServices'
import './LocationMapModal.css'

interface LocationMapModalProps {
  isOpen: boolean
  onClose: () => void
  address: string
  title?: string
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
 * Modal wyświetlający podgląd lokalizacji gabinetu lub wizyty na interaktywnej mapie OpenStreetMap / Leaflet.
 */
export const LocationMapModal: React.FC<LocationMapModalProps> = ({
  isOpen,
  onClose,
  address,
  title = 'Lokalizacja wizyty',
}) => {
  const mapContainerRef = useRef<HTMLDivElement | null>(null)
  const mapRef = useRef<L.Map | null>(null)
  const markerRef = useRef<L.Marker | null>(null)

  const [coords, setCoords] = useState<{ lat: number; lon: number }>({
    lat: DEFAULT_CENTER.lat,
    lon: DEFAULT_CENTER.lon,
  })

  useEffect(() => {
    if (isOpen && address.trim()) {
      searchAddress(address).then((results) => {
        if (results.length > 0) {
          setCoords({ lat: results[0].lat, lon: results[0].lon })
        }
      })
    }
  }, [isOpen, address])

  useEffect(() => {
    if (!isOpen || !mapContainerRef.current) return

    if (!mapRef.current) {
      const map = L.map(mapContainerRef.current, {
        center: [coords.lat, coords.lon],
        zoom: 15,
        zoomControl: true,
      })

      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 19,
        attribution: '&copy; OpenStreetMap contributors',
      }).addTo(map)

      const marker = L.marker([coords.lat, coords.lon], {
        icon: createCustomPinIcon(),
      }).addTo(map)

      marker.bindPopup(`<b>${title}</b><br/>${address}`).openPopup()

      mapRef.current = map
      markerRef.current = marker
    } else {
      mapRef.current.setView([coords.lat, coords.lon], 15)
      if (markerRef.current) {
        markerRef.current.setLatLng([coords.lat, coords.lon])
        markerRef.current.setPopupContent(`<b>${title}</b><br/>${address}`)
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
  }, [isOpen, coords, address, title])

  if (!isOpen) return null

  return (
    <div className="location-view-overlay" onClick={onClose} role="dialog" aria-modal="true">
      <div className="location-view-card" onClick={(e) => e.stopPropagation()}>
        <header className="location-view-header">
          <div className="location-view-title">
            <h3>{title}</h3>
            <p className="location-view-address">{address || 'Brak wyznaczonego adresu'}</p>
          </div>
          <button className="location-view-close" onClick={onClose} aria-label="Zamknij modal">
            &times;
          </button>
        </header>

        <div className="location-view-map-container">
          <div ref={mapContainerRef} className="location-view-map-element" />
        </div>

        <footer className="location-view-footer">
          <button type="button" className="location-picker-cancel-btn" onClick={onClose}>
            Zamknij
          </button>
          <button
            type="button"
            className="location-view-navigate-btn"
            onClick={() => openInGoogleMaps(address || coords)}
          >
            <svg
              width="18"
              height="18"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
            >
              <polygon points="3 11 22 2 13 21 11 13 3 11"></polygon>
            </svg>
            Otwórz w Google Maps / Jak dojechać
          </button>
        </footer>
      </div>
    </div>
  )
}
