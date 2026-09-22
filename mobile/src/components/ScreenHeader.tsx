/**
 * @file ScreenHeader.tsx
 * @description Nagłówek ekranów aplikacji mobilnej oraz uniwersalny kontener karty sekcji (SectionCard).
 */

import type { ReactNode } from 'react'
import { StyleSheet, Text, View, type ViewProps } from 'react-native'

import { colors, radius, space, typography } from '@/theme/tokens'

/** Właściwości komponentu {@link ScreenHeader}. */
interface ScreenHeaderProps extends ViewProps {
  /** Główny tytuł ekranu. */
  title: string
  /** Opcjonalny podtytuł lub opis ekranu. */
  subtitle?: string
}

/**
 * Standardowy nagłówek ekranu prezentujący tytuł oraz opcjonalny podtytuł.
 *
 * @param props Właściwości nagłówka ekranu.
 * @returns Element React Native prezentujący nagłówek.
 */
export function ScreenHeader({ title, subtitle, style, ...rest }: ScreenHeaderProps) {
  return (
    <View style={[styles.wrap, style]} {...rest}>
      <Text style={styles.title}>{title}</Text>
      {subtitle ? <Text style={styles.subtitle}>{subtitle}</Text> : null}
    </View>
  )
}

/**
 * Kartowy kontener sekcji ze spójnymi odstępami i obramowaniem.
 *
 * @param props Właściwości kontenera sekcji.
 * @returns Element React Native będący kartą widoku.
 */
export function SectionCard({ children, style, ...rest }: ViewProps & { children: ReactNode }) {
  return (
    <View style={[styles.card, style]} {...rest}>
      {children}
    </View>
  )
}

const styles = StyleSheet.create({
  wrap: {
    gap: space.xs,
    marginBottom: space.base,
  },
  title: {
    fontSize: typography['2xl'],
    fontWeight: '700',
    color: colors.ink,
  },
  subtitle: {
    fontSize: typography.sm,
    color: colors.muted,
  },
  card: {
    backgroundColor: colors.surface,
    borderRadius: radius.lg,
    borderWidth: 1,
    borderColor: colors.border,
    padding: space.base,
    gap: space.md,
  },
})
