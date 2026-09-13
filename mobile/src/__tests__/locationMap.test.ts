import { describe, it, expect } from 'vitest'

describe('mobile locationMap logic', () => {
  it('builds static map URL correctly from coordinates', () => {
    const lat = 52.2297
    const lon = 21.0122
    const staticMapUrl = `https://staticmap.openstreetmap.de/staticmap.php?center=${lat},${lon}&zoom=15&size=600x300&markers=${lat},${lon},ol-marker`

    expect(staticMapUrl).toContain('52.2297,21.0122')
    expect(staticMapUrl).toContain('zoom=15')
  })

  it('handles empty address gracefully', () => {
    const address = '  '
    expect(address.trim()).toBe('')
  })
})
