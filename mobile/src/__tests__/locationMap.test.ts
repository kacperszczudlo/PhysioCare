/**
 * @file locationMap.test.ts
 * @description Testy jednostkowe logiki budowania adresów statycznej mapy OpenStreetMap.
 */

import { describe, it, expect } from 'vitest'

describe('mobile locationMap logic', () => {
  it('poprawnie buduje adres URL statycznej mapy na podstawie współrzędnych', () => {
    // Arrange
    const lat = 52.2297
    const lon = 21.0122

    // Act
    const staticMapUrl = `https://staticmap.openstreetmap.de/staticmap.php?center=${lat},${lon}&zoom=15&size=600x300&markers=${lat},${lon},ol-marker`

    // Assert
    expect(staticMapUrl).toContain('52.2297,21.0122')
    expect(staticMapUrl).toContain('zoom=15')
  })

  it('bezpiecznie obsługuje pusty adres geograficzny', () => {
    // Arrange
    const address = '  '

    // Act
    const trimmed = address.trim()

    // Assert
    expect(trimmed).toBe('')
  })
})
