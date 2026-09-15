import { describe, it, expect } from 'vitest'
import { visitStatusLabel, consentLabel, isRequiredConsent, formatTimeRange } from '../lib/format'

describe('format (Mobile)', () => {
  it('translates visit status codes to human Polish labels', () => {
    expect(visitStatusLabel('PENDING_APPROVAL')).toBe('Oczekuje na zatwierdzenie')
    expect(visitStatusLabel('SCHEDULED')).toBe('Zaplanowana')
    expect(visitStatusLabel('COMPLETED')).toBe('Zakończona')
    expect(visitStatusLabel('CANCELLED')).toBe('Odwołana')
    expect(visitStatusLabel('NO_SHOW')).toBe('Nieobecność')
    expect(visitStatusLabel('UNKNOWN')).toBe('UNKNOWN')
  })

  it('identifies required RODO consents', () => {
    expect(isRequiredConsent('TERMS_REQUIRED')).toBe(true)
    expect(isRequiredConsent('MEDICAL_DATA_REQUIRED')).toBe(true)
    expect(isRequiredConsent('MARKETING_OPTIONAL')).toBe(false)
  })

  it('formats consent labels', () => {
    expect(consentLabel('TERMS_REQUIRED')).toBe('Regulamin')
    expect(consentLabel('MARKETING_OPTIONAL')).toBe('Marketing')
  })

  it('formats time range between start and end ISO', () => {
    const start = '2026-09-14T10:00:00.000Z'
    const end = '2026-09-14T10:45:00.000Z'
    const formatted = formatTimeRange(start, end)
    expect(formatted).toContain('-')
  })
})
