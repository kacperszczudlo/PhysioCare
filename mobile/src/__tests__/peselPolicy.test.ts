import { describe, it, expect } from 'vitest'
import { getPeselError, PESEL_MESSAGES } from '../lib/peselPolicy'

describe('peselPolicy (Mobile)', () => {
  it('validates a correct PESEL checksum (92071304259)', () => {
    const error = getPeselError('92071304259')
    expect(error).toBeNull()
  })

  it('rejects empty PESEL when allowBlank is false', () => {
    const error = getPeselError('', { allowBlank: false })
    expect(error).toBe(PESEL_MESSAGES.required)
  })

  it('rejects PESEL with invalid checksum', () => {
    const error = getPeselError('92071304250')
    expect(error).toBe(PESEL_MESSAGES.invalidChecksum)
  })
})
