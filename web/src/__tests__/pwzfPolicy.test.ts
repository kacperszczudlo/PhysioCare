import { describe, it, expect } from 'vitest'
import { getPwzfError, normalizePwzf, PWZF_MESSAGES } from '../lib/pwzfPolicy'

/**
 * Zestaw testów jednostkowych weryfikujących format i walidację 5-cyfrowego numeru PWZF fizjoterapeuty.
 */
describe('pwzfPolicy (Web)', () => {
  it('normalizes PWZF string with prefix', () => {
    // Arrange & Act & Assert
    expect(normalizePwzf('PWZFz 71239')).toBe('71239')
    expect(normalizePwzf('pwzf nr. 71239')).toBe('71239')
  })

  it('validates a valid 5-digit PWZF number', () => {
    // Arrange & Act
    const error = getPwzfError('71239')

    // Assert
    expect(error).toBeNull()
  })

  it('rejects empty PWZF', () => {
    // Arrange & Act
    const error = getPwzfError('')

    // Assert
    expect(error).toBe(PWZF_MESSAGES.required)
  })

  it('rejects PWZF with incorrect digit count', () => {
    // Arrange & Act
    const error = getPwzfError('1234')

    // Assert
    expect(error).toBe(PWZF_MESSAGES.invalid)
  })
})
