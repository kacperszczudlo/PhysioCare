import { describe, it, expect, vi } from 'vitest'
import {
  formatAddressFromNominatim,
  openInGoogleMaps,
  searchAddress,
} from '../components/location/locationServices'

describe('locationServices', () => {
  it('formats Polish address cleanly from Nominatim details', () => {
    const details = {
      address: {
        road: 'Marszałkowska',
        house_number: '10',
        city: 'Warszawa',
        postcode: '00-001',
      },
      display_name: 'Marszałkowska 10, 00-001 Warszawa, Polska',
    }

    const formatted = formatAddressFromNominatim(details)
    expect(formatted).toBe('Marszałkowska 10, 00-001 Warszawa')
  })

  it('handles address with town or village when city is missing', () => {
    const details = {
      address: {
        road: 'Główna',
        house_number: '5',
        town: 'Piaseczno',
        postcode: '05-500',
      },
    }

    const formatted = formatAddressFromNominatim(details)
    expect(formatted).toBe('Główna 5, 05-500 Piaseczno')
  })

  it('falls back to display_name when address details are empty', () => {
    const details = {
      address: {},
      display_name: 'Rynek Główny, Kraków',
    }

    const formatted = formatAddressFromNominatim(details)
    expect(formatted).toBe('Rynek Główny, Kraków')
  })

  it('returns empty array when search query is shorter than 3 chars', async () => {
    const results = await searchAddress('ul')
    expect(results).toEqual([])
  })

  it('opens Google Maps in a new tab with query string or coordinates', () => {
    const windowSpy = vi.spyOn(window, 'open').mockImplementation(() => null)

    openInGoogleMaps('ul. Marszałkowska 10, Warszawa')
    expect(windowSpy).toHaveBeenCalledWith(
      'https://www.google.com/maps/search/?api=1&query=ul.%20Marsza%C5%82kowska%2010%2C%20Warszawa',
      '_blank',
      'noopener,noreferrer',
    )

    openInGoogleMaps({ lat: 52.2297, lon: 21.0122 })
    expect(windowSpy).toHaveBeenCalledWith(
      'https://www.google.com/maps/search/?api=1&query=52.2297,21.0122',
      '_blank',
      'noopener,noreferrer',
    )

    windowSpy.mockRestore()
  })
})
