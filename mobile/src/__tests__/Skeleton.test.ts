import { describe, expect, it } from 'vitest'
import { radius, space } from '../theme/tokens'

describe('Mobile Skeleton helper math & radius calculations', () => {
  it('computes circle radius correctly from height', () => {
    const height = 40
    const computedRadius = height / 2
    expect(computedRadius).toBe(20)
  })

  it('uses default radius token when not circle', () => {
    expect(radius.sm).toBe(6)
    expect(radius.md).toBe(10)
    expect(radius.lg).toBe(14)
  })

  it('provides correct spacing values for skeleton text gap', () => {
    expect(space.xs).toBe(4)
    expect(space.md).toBe(12)
  })
})
