/**
 * @file locationMap.test.ts
 * @description Testy jednostkowe logiki kafelków OpenStreetMap oraz normalizacji adresów dla karty lokalizacji.
 */

import { describe, expect, it } from 'vitest'
import { buildOsmTileGrid, latLonToTileCoords, stripPolishPostalCode } from '../lib/osmMap'

describe('mobile locationMap logic', () => {
  it('computes Web Mercator tile coordinates and pixel offsets for Suwałki', () => {
    const { tileX, tileY, pixelX, pixelY } = latLonToTileCoords(54.1115, 22.9308, 15)

    expect(tileX).toBe(18471)
    expect(tileY).toBe(10503)
    expect(pixelX).toBeGreaterThanOrEqual(0)
    expect(pixelX).toBeLessThan(256)
    expect(pixelY).toBeGreaterThanOrEqual(0)
    expect(pixelY).toBeLessThan(256)
  })

  it('builds a 3x3 OpenStreetMap tile grid centered on the target coordinates', () => {
    const tiles = buildOsmTileGrid(54.1115, 22.9308, 15)

    expect(tiles).toHaveLength(9)
    expect(tiles[0]?.url).toMatch(/^https:\/\/tile\.openstreetmap\.org\/15\/\d+\/\d+\.png$/)
    const centerTile = tiles[4]!
    expect(centerTile.offsetLeft).toBeGreaterThan(-256)
    expect(centerTile.offsetLeft).toBeLessThanOrEqual(0)
    expect(centerTile.offsetTop).toBeGreaterThan(-256)
    expect(centerTile.offsetTop).toBeLessThanOrEqual(0)
  })

  it('strips Polish postal code for fallback Nominatim geocoding', () => {
    expect(stripPolishPostalCode('Szpitalna 60, 16-400 Suwałki')).toBe('Szpitalna 60, Suwałki')
    expect(stripPolishPostalCode('  ')).toBe('')
  })
})
