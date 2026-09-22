/** Struktura wybranego wyniku geokodowania adresu. */
export interface LocationAddressResult {
  place_id: number
  display_name: string
  lat: number
  lon: number
  formatted_address: string
  city?: string
  street?: string
  postcode?: string
}

/** Odpowiedź ze szczegółami adresu z API Nominatim (OpenStreetMap). */
export interface NominatimAddressDetails {
  road?: string
  pedestrian?: string
  street?: string
  suburb?: string
  house_number?: string
  city?: string
  town?: string
  village?: string
  municipality?: string
  postcode?: string
}

export interface NominatimItem {
  place_id: number
  display_name: string
  lat: string
  lon: string
  error?: string
  address?: NominatimAddressDetails
}

/** Domyślny punkt środkowy mapy (Warszawa Centrum). */
export const DEFAULT_CENTER = {
  lat: 52.2297,
  lon: 21.0122,
}

/**
 * Formatuj surowe szczegóły adresu OpenStreetMap/Nominatim na czytelny polski adres (np. "ul. Kwiatowa 12, 00-001 Warszawa").
 *
 * @param details - Szczegóły obiektu adresu z API OpenStreetMap.
 * @returns Sformatowany ciąg znaków adresu.
 */
export function formatAddressFromNominatim(details: {
  address?: NominatimAddressDetails
  display_name?: string
}): string {
  if (!details) return ''
  const addr = details.address || {}

  const road = addr.road || addr.pedestrian || addr.street || addr.suburb || ''
  const houseNumber = addr.house_number || ''
  const city = addr.city || addr.town || addr.village || addr.municipality || ''
  const postcode = addr.postcode || ''

  const streetPart = road ? (houseNumber ? `${road} ${houseNumber}` : road) : ''
  const cityPart = postcode ? (city ? `${postcode} ${city}` : postcode) : city

  if (streetPart && cityPart) {
    return `${streetPart}, ${cityPart}`
  } else if (streetPart) {
    return streetPart
  } else if (cityPart) {
    return cityPart
  }

  return details.display_name || ''
}

export async function searchAddress(
  query: string,
  signal?: AbortSignal,
): Promise<LocationAddressResult[]> {
  const trimmed = query.trim()
  if (!trimmed || trimmed.length < 3) return []

  const url = `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(
    trimmed,
  )}&addressdetails=1&limit=6&accept-language=pl,en`

  try {
    const res = await fetch(url, {
      signal,
      headers: {
        'Accept-Language': 'pl,en',
        'User-Agent': 'PhysioCare-App/1.0',
      },
    })
    if (!res.ok) return []

    const data: NominatimItem[] = await res.json()
    if (!Array.isArray(data)) return []

    return data.map((item) => ({
      place_id: item.place_id,
      display_name: item.display_name,
      lat: parseFloat(item.lat),
      lon: parseFloat(item.lon),
      formatted_address: formatAddressFromNominatim(item),
      city: item.address?.city || item.address?.town || item.address?.village,
      street: item.address?.road,
      postcode: item.address?.postcode,
    }))
  } catch (err) {
    if (err instanceof Error && err.name === 'AbortError') {
      return []
    }
    console.warn('Geocoding search error:', err)
    return []
  }
}

export async function reverseGeocode(
  lat: number,
  lon: number,
  signal?: AbortSignal,
): Promise<LocationAddressResult | null> {
  const url = `https://nominatim.openstreetmap.org/reverse?format=json&lat=${lat}&lon=${lon}&addressdetails=1&accept-language=pl,en`

  try {
    const res = await fetch(url, {
      signal,
      headers: {
        'Accept-Language': 'pl,en',
        'User-Agent': 'PhysioCare-App/1.0',
      },
    })
    if (!res.ok) return null

    const item: NominatimItem = await res.json()
    if (!item || item.error) return null

    return {
      place_id: item.place_id || Date.now(),
      display_name: item.display_name || '',
      lat: parseFloat(item.lat || String(lat)),
      lon: parseFloat(item.lon || String(lon)),
      formatted_address: formatAddressFromNominatim(item),
      city: item.address?.city || item.address?.town || item.address?.village,
      street: item.address?.road,
      postcode: item.address?.postcode,
    }
  } catch (err) {
    if (err instanceof Error && err.name === 'AbortError') {
      return null
    }
    console.warn('Reverse geocoding error:', err)
    return null
  }
}

export function openInGoogleMaps(addressOrCoords: string | { lat: number; lon: number }) {
  let query = ''
  if (typeof addressOrCoords === 'string') {
    query = encodeURIComponent(addressOrCoords)
  } else {
    query = `${addressOrCoords.lat},${addressOrCoords.lon}`
  }
  const url = `https://www.google.com/maps/search/?api=1&query=${query}`
  window.open(url, '_blank', 'noopener,noreferrer')
}
