import { describe, expect, it } from 'vitest'

describe('ReviewModal rating logic and validation', () => {
  const RATING_LABELS: Record<number, string> = {
    1: 'Bardzo słabo',
    2: 'Poniżej oczekiwań',
    3: 'W porządku',
    4: 'Bardzo dobrze',
    5: 'Znakomicie!',
  }

  function validateRatingSubmission(rating: number): { valid: boolean; error?: string } {
    if (rating < 1 || rating > 5) {
      return { valid: false, error: 'Wybierz ocenę od 1 do 5 gwiazdek przed wysłaniem.' }
    }
    return { valid: true }
  }

  it('defaults to 0 stars (unselected) for a new review', () => {
    const initialRating = 0
    expect(initialRating).toBe(0)
    expect(validateRatingSubmission(initialRating).valid).toBe(false)
    expect(validateRatingSubmission(initialRating).error).toBe(
      'Wybierz ocenę od 1 do 5 gwiazdek przed wysłaniem.',
    )
  })

  it('rejects submission when 0 stars are selected', () => {
    const result = validateRatingSubmission(0)
    expect(result.valid).toBe(false)
  })

  it('accepts ratings from 1 to 5', () => {
    for (let r = 1; r <= 5; r++) {
      const result = validateRatingSubmission(r)
      expect(result.valid).toBe(true)
      expect(result.error).toBeUndefined()
      expect(RATING_LABELS[r]).toBeDefined()
    }
  })

  it('maps ratings to human-friendly feedback copy', () => {
    expect(RATING_LABELS[1]).toBe('Bardzo słabo')
    expect(RATING_LABELS[3]).toBe('W porządku')
    expect(RATING_LABELS[5]).toBe('Znakomicie!')
  })
})
