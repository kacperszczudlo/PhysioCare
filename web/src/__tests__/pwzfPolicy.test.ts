import { describe, it, expect } from 'vitest'
import { getPwzfError, normalizePwzf, PWZF_MESSAGES } from '../lib/pwzfPolicy'

describe('pwzfPolicy (Web)', () => {
  it('normalizes PWZF string with prefix', () => {
    expect(normalizePwzf('PWZFz 71239')).toBe('71239')
    expect(normalizePwzf('pwzf nr. 71239')).toBe('71239')
  })

  it('validates a valid 5-digit PWZF number', () => {
    const error = getPwzfError('71239')
    expect(error).toBeNull()
  })

  it('rejects empty PWZF', () => {
    const error = getPwzfError('')
    expect(error).toBe(PWZF_MESSAGES.required)
  })

  it('rejects PWZF with incorrect digit count', () => {
    const error = getPwzfError('1234')
    expect(error).toBe(PWZF_MESSAGES.invalid)
  })
})
