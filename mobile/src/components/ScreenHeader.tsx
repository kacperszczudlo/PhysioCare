import type { ReactNode } from 'react'
import { StyleSheet, Text, View, type ViewProps } from 'react-native'

import { colors, radius, space, typography } from '@/theme/tokens'

interface ScreenHeaderProps extends ViewProps {
  title: string
  subtitle?: string
}

export function ScreenHeader({ title, subtitle, style, ...rest }: ScreenHeaderProps) {
  return (
    <View style={[styles.wrap, style]} {...rest}>
      <Text style={styles.title}>{title}</Text>
      {subtitle ? <Text style={styles.subtitle}>{subtitle}</Text> : null}
    </View>
  )
}

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
