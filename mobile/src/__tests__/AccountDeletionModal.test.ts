import { describe, expect, it } from 'vitest'

const DELETION_REASON_OPTIONS = [
  { id: 'not_using', label: 'Nie korzystam z aplikacji' },
  { id: 'technical', label: 'Problemy techniczne' },
  { id: 'therapist_change', label: 'Zmiana fizjoterapeuty / gabinetu' },
  { id: 'privacy', label: 'Obawy o prywatność danych' },
  { id: 'other', label: 'Inny powód' },
] as const

describe('AccountDeletionModal validation and reason composition logic', () => {
  function composeReasonPayload(
    reasonId: (typeof DELETION_REASON_OPTIONS)[number]['id'] | null,
    otherText: string,
  ): string {
    if (!reasonId) return ''
    const label = DELETION_REASON_OPTIONS.find((o) => o.id === reasonId)?.label ?? reasonId
    if (reasonId === 'other') {
      const detail = otherText.trim()
      return detail ? `${label}: ${detail}` : label
    }
    return label
  }

  function validateDeletionSubmission(
    reasonId: (typeof DELETION_REASON_OPTIONS)[number]['id'] | null,
    otherText: string,
    confirmed: boolean,
  ): { valid: boolean; error?: string } {
    if (!reasonId) {
      return { valid: false, error: 'Wybierz powód rezygnacji.' }
    }
    if (reasonId === 'other' && !otherText.trim()) {
      return { valid: false, error: 'Opisz krótko powód rezygnacji.' }
    }
    if (!confirmed) {
      return { valid: false, error: 'Potwierdź, że na pewno chcesz usunąć konto.' }
    }
    return { valid: true }
  }

  it('provides all 5 standard deletion reason options', () => {
    expect(DELETION_REASON_OPTIONS).toHaveLength(5)
    const ids = DELETION_REASON_OPTIONS.map((o) => o.id)
    expect(ids).toEqual(['not_using', 'technical', 'therapist_change', 'privacy', 'other'])
  })

  it('rejects submission when no reason is selected', () => {
    const res = validateDeletionSubmission(null, '', true)
    expect(res.valid).toBe(false)
    expect(res.error).toBe('Wybierz powód rezygnacji.')
  })

  it('rejects submission when "other" is selected without description', () => {
    const res = validateDeletionSubmission('other', '   ', true)
    expect(res.valid).toBe(false)
    expect(res.error).toBe('Opisz krótko powód rezygnacji.')
  })

  it('rejects submission when confirmation checkbox is unchecked', () => {
    const res = validateDeletionSubmission('not_using', '', false)
    expect(res.valid).toBe(false)
    expect(res.error).toBe('Potwierdź, że na pewno chcesz usunąć konto.')
  })

  it('correctly composes reason payload for standard option', () => {
    const payload = composeReasonPayload('privacy', '')
    expect(payload).toBe('Obawy o prywatność danych')
  })

  it('correctly composes reason payload for other option with custom details', () => {
    const payload = composeReasonPayload('other', 'Kończę rehabilitację i wracam do zdrowia')
    expect(payload).toBe('Inny powód: Kończę rehabilitację i wracam do zdrowia')
  })

  it('validates successfully when reason and confirmation checkbox are provided', () => {
    const res = validateDeletionSubmission('therapist_change', '', true)
    expect(res.valid).toBe(true)
    expect(res.error).toBeUndefined()
  })
})
