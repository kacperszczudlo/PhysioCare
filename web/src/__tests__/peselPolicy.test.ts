import { describe, it, expect } from 'vitest'
import { getPeselError, PESEL_MESSAGES } from '../lib/peselPolicy'

/**
 * Zestaw testów jednostkowych weryfikujących poprawność sumy kontrolnej i cyfr numeru PESEL pacjenta.
 */
describe('peselPolicy (Web)', () => {
  it('validates a correct PESEL checksum (92071304259)', () => {
    // Arrange
    const pesel = '92071304259'

    // Act
    const error = getPeselError(pesel)

    // Assert
    expect(error).toBeNull()
  })

  it('rejects empty PESEL when allowBlank is false', () => {
    // Arrange & Act
    const error = getPeselError('', { allowBlank: false })

    // Assert
    expect(error).toBe(PESEL_MESSAGES.required)
  })

  it('rejects PESEL with invalid length', () => {
    // Arrange & Act
    const error = getPeselError('12345')

    // Assert
    expect(error).toBe(PESEL_MESSAGES.invalidFormat)
  })

  it('rejects PESEL with incorrect checksum', () => {
    // Arrange & Act
    const error = getPeselError('92071304250')

    // Assert
    expect(error).toBe(PESEL_MESSAGES.invalidChecksum)
  })

  it('rejects PESEL exceeding 11 characters', () => {
    // Arrange & Act
    const error = getPeselError('1234567890123')

    // Assert
    expect(error).toBe(PESEL_MESSAGES.tooLong)
  })
})
