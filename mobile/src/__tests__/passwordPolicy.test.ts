/**
 * @file passwordPolicy.test.ts
 * @description Testy jednostkowe polityki haseł (walidacja długości, cyfr, znaków specjalnych oraz powtórzenia hasła).
 */

import { describe, it, expect } from 'vitest'
import {
  getPasswordError,
  getPasswordRequirements,
  passwordsMatch,
  PASSWORD_MESSAGES,
} from '../lib/passwordPolicy'

describe('passwordPolicy (Mobile)', () => {
  it('poprawnie waliduje silne hasło', () => {
    // Arrange & Act
    const error = getPasswordError('Haslo123!')

    // Assert
    expect(error).toBeNull()
  })

  it('odrzuca puste hasło', () => {
    // Arrange & Act
    const error = getPasswordError('')

    // Assert
    expect(error).toBe(PASSWORD_MESSAGES.required)
  })

  it('odrzuca zbyt krótkie hasła', () => {
    // Arrange & Act
    const error = getPasswordError('H1!')

    // Assert
    expect(error).toBe(PASSWORD_MESSAGES.tooShort)
  })

  it('odrzuca hasła składające się wyłącznie z cyfr', () => {
    // Arrange & Act
    const error = getPasswordError('123456789')

    // Assert
    expect(error).toBe(PASSWORD_MESSAGES.entirelyNumeric)
  })

  it('generuje i weryfikuje listę wymagań dla podanego hasła', () => {
    // Arrange & Act
    const reqs = getPasswordRequirements('Haslo123!')

    // Assert
    expect(reqs.length).toBeGreaterThan(0)
    expect(reqs.every((r) => r.met)).toBe(true)
  })

  it('weryfikuje zgodność powtórzonego hasła', () => {
    // Arrange & Act & Assert
    expect(passwordsMatch('Haslo123!', 'Haslo123!')).toBe(true)
    expect(passwordsMatch('Haslo123!', 'Inne123!')).toBe(false)
  })
})
