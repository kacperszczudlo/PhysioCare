export const TILE_SIZE = 256
export const DEFAULT_MAP_ZOOM = 15

export interface OsmTileItem {
  key: string
  url: string
  /** Poziome przesunięcie kafelka w pikselach względem środka docelowej współrzędnej. */
  offsetLeft: number
  /** Pionowe przesunięcie kafelka w pikselach względem środka docelowej współrzędnej. */
  offsetTop: number
}

/**
 * Konwertuje współrzędne geograficzne (lat, lon) na indeks kafelka Web Mercator oraz przesunięcie pikselowe wewnątrz kafelka.
 */
export function latLonToTileCoords(
  lat: number,
  lon: number,
  zoom = DEFAULT_MAP_ZOOM,
): { tileX: number; tileY: number; pixelX: number; pixelY: number } {
  const n = 2 ** zoom
  const clampedLat = Math.max(-85.05112878, Math.min(85.05112878, lat))
  const latRad = (clampedLat * Math.PI) / 180
  const xFloat = ((lon + 180) / 360) * n
  const yFloat = ((1 - Math.log(Math.tan(latRad) + 1 / Math.cos(latRad)) / Math.PI) / 2) * n

  const tileX = Math.floor(xFloat)
  const tileY = Math.floor(yFloat)

  return {
    tileX,
    tileY,
    pixelX: (xFloat - tileX) * TILE_SIZE,
    pixelY: (yFloat - tileY) * TILE_SIZE,
  }
}

/**
 * Buduje siatkę 3x3 kafelków OpenStreetMap wyśrodkowaną dokładnie na punkcie (lat, lon).
 */
export function buildOsmTileGrid(lat: number, lon: number, zoom = DEFAULT_MAP_ZOOM): OsmTileItem[] {
  const n = 2 ** zoom
  const { tileX, tileY, pixelX, pixelY } = latLonToTileCoords(lat, lon, zoom)
  const tiles: OsmTileItem[] = []

  for (let dy = -1; dy <= 1; dy += 1) {
    const y = tileY + dy
    if (y < 0 || y >= n) continue

    for (let dx = -1; dx <= 1; dx += 1) {
      const x = (((tileX + dx) % n) + n) % n
      tiles.push({
        key: `${zoom}-${x}-${y}`,
        url: `https://tile.openstreetmap.org/${zoom}/${x}/${y}.png`,
        offsetLeft: dx * TILE_SIZE - pixelX,
        offsetTop: dy * TILE_SIZE - pixelY,
      })
    }
  }

  return tiles
}

/**
 * Usuwa polski kod pocztowy (np. `16-400`) jako zapasowe zapytanie dla geokodera Nominatim.
 */
export function stripPolishPostalCode(address: string): string {
  return address
    .replace(/\b\d{2}-\d{3}\b/g, '')
    .replace(/\s*,\s*,+/g, ',')
    .replace(/\s{2,}/g, ' ')
    .trim()
}
