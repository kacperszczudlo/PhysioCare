import type { ReactNode } from 'react'
import { ActivityIndicator, Pressable, StyleSheet, Text, View } from 'react-native'

import { colors, radius, space, typography } from '@/theme/tokens'
import { Button } from './Button'

export function LoadingBlock({ label = 'Ładowanie…', skeleton }: { label?: string; skeleton?: ReactNode }) {
  if (skeleton) {
    return (
      <View accessibilityLabel={label} accessibilityState={{ busy: true }}>
        {skeleton}
      </View>
    )
  }
  return (
    <View style={styles.center} accessibilityLabel={label}>
      <ActivityIndicator size="large" color={colors.primary} />
      <Text style={styles.muted}>{label}</Text>
    </View>
  )
}

export function ErrorBanner({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <View style={styles.errorBox} accessibilityRole="alert">
      <Text style={styles.errorText}>{message}</Text>
      {onRetry ? (
        <Pressable onPress={onRetry} accessibilityRole="button">
          <Text style={styles.retry}>Spróbuj ponownie</Text>
        </Pressable>
      ) : null}
    </View>
  )
}

export function SuccessBanner({ message }: { message: string }) {
  return (
    <View style={styles.successBox} accessibilityRole="text" accessibilityLiveRegion="polite">
      <Text style={styles.successText}>{message}</Text>
    </View>
  )
}

export function EmptyState({
  title,
  description,
  actionLabel,
  onAction,
}: {
  title: string
  description?: string
  actionLabel?: string
  onAction?: () => void
}) {
  return (
    <View style={styles.empty}>
      <Text style={styles.emptyTitle}>{title}</Text>
      {description ? <Text style={styles.muted}>{description}</Text> : null}
      {actionLabel && onAction ? (
        <Button title={actionLabel} onPress={onAction} variant="secondary" />
      ) : null}
    </View>
  )
}

const styles = StyleSheet.create({
  center: {
    alignItems: 'center',
    justifyContent: 'center',
    gap: space.md,
    paddingVertical: space['3xl'],
  },
  muted: {
    color: colors.muted,
    fontSize: typography.sm,
    textAlign: 'center',
  },
  errorBox: {
    backgroundColor: colors.dangerSubtle,
    borderRadius: radius.md,
    padding: space.base,
    gap: space.sm,
    borderWidth: 1,
    borderColor: colors.danger,
  },
  errorText: {
    color: colors.danger,
    fontSize: typography.sm,
    fontWeight: '600',
  },
  retry: {
    color: colors.danger,
    fontWeight: '700',
    fontSize: typography.sm,
  },
  successBox: {
    backgroundColor: colors.successSubtle,
    borderRadius: radius.md,
    padding: space.base,
    borderWidth: 1,
    borderColor: colors.success,
  },
  successText: {
    color: colors.success,
    fontSize: typography.sm,
    fontWeight: '700',
  },
  empty: {
    alignItems: 'center',
    gap: space.md,
    paddingVertical: space['3xl'],
    paddingHorizontal: space.base,
  },
  emptyTitle: {
    fontSize: typography.lg,
    fontWeight: '700',
    color: colors.ink,
    textAlign: 'center',
  },
})
