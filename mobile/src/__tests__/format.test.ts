/**
 * @file format.test.ts
 * @description Testy jednostkowe funkcji formatowania statusów wizyt, etykiet zgód RODO i zakresów czasowych.
 */

import { describe, it, expect } from 'vitest'
import { visitStatusLabel, consentLabel, isRequiredConsent, formatTimeRange } from '../lib/format'

describe('format (Mobile)', () => {
  it('tłumaczy kody statusu wizyty na czytelne polskie etykiety', () => {
    // Arrange & Act & Assert
    expect(visitStatusLabel('PENDING_APPROVAL')).toBe('Oczekuje na zatwierdzenie')
    expect(visitStatusLabel('SCHEDULED')).toBe('Zaplanowana')
    expect(visitStatusLabel('COMPLETED')).toBe('Zakończona')
    expect(visitStatusLabel('CANCELLED')).toBe('Odwołana')
    expect(visitStatusLabel('NO_SHOW')).toBe('Nieobecność')
    expect(visitStatusLabel('UNKNOWN')).toBe('UNKNOWN')
  })

  it('poprawnie rozpoznacza wymagane zgody RODO', () => {
    // Arrange & Act & Assert
    expect(isRequiredConsent('TERMS_REQUIRED')).toBe(true)
    expect(isRequiredConsent('MEDICAL_DATA_REQUIRED')).toBe(true)
    expect(isRequiredConsent('MARKETING_OPTIONAL')).toBe(false)
  })

  it('formatuje etykiety tekstowe dla typów zgód', () => {
    // Arrange & Act & Assert
    expect(consentLabel('TERMS_REQUIRED')).toBe('Regulamin')
    expect(consentLabel('MARKETING_OPTIONAL')).toBe('Marketing')
  })

  it('formatuje przedział czasowy między ISO start i end', () => {
    // Arrange
    const start = '2026-09-14T10:00:00.000Z'
    const end = '2026-09-14T10:45:00.000Z'

    // Act
    const formatted = formatTimeRange(start, end)

    // Assert
    expect(formatted).toContain('-')
  })
})
