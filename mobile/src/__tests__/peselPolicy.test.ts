/**
 * @file peselPolicy.test.ts
 * @description Testy jednostkowe weryfikacji poprawności cyfry kontrolnej i formatu numeru PESEL.
 */

import { describe, it, expect } from 'vitest'
import { getPeselError, PESEL_MESSAGES } from '../lib/peselPolicy'

describe('peselPolicy (Mobile)', () => {
  it('poprawnie waliduje prawidłową cyfrę kontrolną PESEL (92071304259)', () => {
    // Arrange & Act
    const error = getPeselError('92071304259')

    // Assert
    expect(error).toBeNull()
  })

  it('odrzuca pusty numer PESEL gdy allowBlank jest false', () => {
    // Arrange & Act
    const error = getPeselError('', { allowBlank: false })

    // Assert
    expect(error).toBe(PESEL_MESSAGES.required)
  })

  it('odrzuca numer PESEL z błędną sumą kontrolną', () => {
    // Arrange & Act
    const error = getPeselError('92071304250')

    // Assert
    expect(error).toBe(PESEL_MESSAGES.invalidChecksum)
  })
})
