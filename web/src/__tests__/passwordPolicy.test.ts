import { describe, it, expect } from 'vitest'
import { getPasswordError, passwordsMatch, PASSWORD_MESSAGES } from '../lib/passwordPolicy'

/**
 * Zestaw testów jednostkowych weryfikujących wymogi złożoności i bezpieczeństwa haseł użytkowników.
 */
describe('passwordPolicy (Web)', () => {
  it('validates a strong password successfully', () => {
    // Arrange
    const password = 'Haslo123!'

    // Act
    const error = getPasswordError(password)

    // Assert
    expect(error).toBeNull()
  })

  it('rejects empty password', () => {
    // Arrange & Act
    const error = getPasswordError('')

    // Assert
    expect(error).toBe(PASSWORD_MESSAGES.required)
  })

  it('rejects passwords that are too short', () => {
    // Arrange & Act
    const error = getPasswordError('H1!')

    // Assert
    expect(error).toBe(PASSWORD_MESSAGES.tooShort)
  })

  it('rejects passwords consisting entirely of numbers', () => {
    // Arrange & Act
    const error = getPasswordError('123456789')

    // Assert
    expect(error).toBe(PASSWORD_MESSAGES.entirelyNumeric)
  })

  it('rejects passwords missing special characters', () => {
    // Arrange & Act
    const error = getPasswordError('Haslo12345')

    // Assert
    expect(error).toBe(PASSWORD_MESSAGES.noSpecial)
  })

  it('detects passwords too similar to user hints', () => {
    // Arrange
    const password = 'JanKowalski123!'
    const userHint = { firstName: 'Jan', lastName: 'Kowalski' }

    // Act
    const error = getPasswordError(password, userHint)

    // Assert
    expect(error).toBe(PASSWORD_MESSAGES.tooSimilar)
  })

  it('verifies passwords match check', () => {
    // Arrange & Act & Assert
    expect(passwordsMatch('Haslo123!', 'Haslo123!')).toBe(true)
    expect(passwordsMatch('Haslo123!', 'InneHaslo123!')).toBe(false)
  })
})
