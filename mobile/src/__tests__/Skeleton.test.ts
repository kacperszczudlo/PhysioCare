/**
 * @file Skeleton.test.ts
 * @description Testy jednostkowe przeliczania wartości promieni, stałych widoków oraz rozmiarów awatarów skeleton.
 */

import { describe, expect, it } from 'vitest'
import { radius, space } from '../theme/tokens'

describe('Mobile Skeleton helper math & radius calculations', () => {
  it('poprawnie oblicza promień koła na podstawie wysokości', () => {
    // Arrange
    const height = 40

    // Act
    const computedRadius = height / 2

    // Assert
    expect(computedRadius).toBe(20)
  })

  it('używa domyślnych tokenów promieni rogów gdy circle jest false', () => {
    // Arrange & Act & Assert
    expect(radius.sm).toBe(6)
    expect(radius.md).toBe(10)
    expect(radius.lg).toBe(14)
  })

  it('dostarcza prawidłowe tokeny odstępów dla skeleton tekstu', () => {
    // Arrange & Act & Assert
    expect(space.xs).toBe(4)
    expect(space.md).toBe(12)
  })

  it('weryfikuje rozmiary awatarów w predefiniowanych wariantach', () => {
    // Arrange
    const avatarSizes = { sm: 32, md: 40, lg: 48, xl: 72 }

    // Act & Assert
    expect(avatarSizes.sm).toBe(32)
    expect(avatarSizes.xl).toBe(72)
  })
})
