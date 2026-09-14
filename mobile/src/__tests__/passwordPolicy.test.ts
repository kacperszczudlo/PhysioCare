import { describe, it, expect } from 'vitest'
import {
  getPasswordError,
  getPasswordRequirements,
  passwordsMatch,
  PASSWORD_MESSAGES,
} from '../lib/passwordPolicy'

describe('passwordPolicy (Mobile)', () => {
  it('validates a strong password successfully', () => {
    const error = getPasswordError('Haslo123!')
    expect(error).toBeNull()
  })

  it('rejects empty password', () => {
    const error = getPasswordError('')
    expect(error).toBe(PASSWORD_MESSAGES.required)
  })

  it('rejects passwords that are too short', () => {
    const error = getPasswordError('H1!')
    expect(error).toBe(PASSWORD_MESSAGES.tooShort)
  })

  it('rejects numeric passwords', () => {
    const error = getPasswordError('123456789')
    expect(error).toBe(PASSWORD_MESSAGES.entirelyNumeric)
  })

  it('verifies passwords match check', () => {
    expect(passwordsMatch('Haslo123!', 'Haslo123!')).toBe(true)
    expect(passwordsMatch('Haslo123!', 'Inne123!')).toBe(false)
  })
})
