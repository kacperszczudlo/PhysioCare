import { describe, it, expect } from 'vitest'
import {
  getPhoneError,
  formatPhoneForApi,
  parseStoredPhone,
  PHONE_MESSAGES,
} from '../lib/phonePolicy'

/**
 * Zestaw testów jednostkowych weryfikujących formatowanie międzynarodowe i walidację polskich numerów telefonów.
 */
describe('phonePolicy (Web)', () => {
  it('formats phone for API correctly', () => {
    // Arrange & Act
    const formatted = formatPhoneForApi('123456789', 'PL')

    // Assert
    expect(formatted).toBe('+48123456789')
  })

  it('parses stored phone into parts', () => {
    // Arrange & Act
    const parts = parseStoredPhone('+48123456789')

    // Assert
    expect(parts.countryCode).toBe('PL')
    expect(parts.nationalNumber).toBe('123456789')
  })

  it('validates a valid national phone number', () => {
    // Arrange & Act
    const error = getPhoneError('123456789', 'PL')

    // Assert
    expect(error).toBeNull()
  })

  it('rejects phone number starting with zero or too short', () => {
    // Arrange & Act
    const error = getPhoneError('012', 'PL')

    // Assert
    expect(error).toBe(PHONE_MESSAGES.invalid)
  })
})
