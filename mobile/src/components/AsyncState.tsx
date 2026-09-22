/**
 * @file AsyncState.tsx
 * @description Komponenty pomocnicze prezentujące stany asynchroniczne interfejsu użytkownika (ładowanie, błędne wykonanie, komunikat sukcesu, informacja oraz pusty stan).
 */

import type { ReactNode } from 'react'
import { ActivityIndicator, Pressable, StyleSheet, Text, View } from 'react-native'

import { colors, radius, space, typography } from '@/theme/tokens'
import { Button } from './Button'

/**
 * Blok wskaźnika ładowania danych z opcjonalnym podglądem szkieletu UI.
 *
 * @param props.label - Etykieta tekstu ładowania (domyślnie "Ładowanie…").
 * @param props.skeleton - Opcjonalny komponent szkieletowy (Skeleton).
 */
export function LoadingBlock({
  label = 'Ładowanie…',
  skeleton,
}: {
  label?: string
  skeleton?: ReactNode
}) {
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

/**
 * Komponent baneru komunikatu błędu z przyciskiem ponowienia operacji.
 *
 * @param props.message - Treść komunikatu błędu.
 * @param props.onRetry - Opcjonalny callback ponowienia akcji.
 */
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

/**
 * Komponent baneru pomyślnej operacji.
 *
 * @param props.message - Treść komunikatu sukcesu.
 */
export function SuccessBanner({ message }: { message: string }) {
  return (
    <View style={styles.successBox} accessibilityRole="text" accessibilityLiveRegion="polite">
      <Text style={styles.successText}>{message}</Text>
    </View>
  )
}

/**
 * Komponent baneru informacyjnego.
 *
 * @param props.message - Treść wiadomości informacyjnej.
 */
export function InfoBanner({ message }: { message: string }) {
  return (
    <View style={styles.infoBox} accessibilityRole="text" accessibilityLiveRegion="polite">
      <Text style={styles.infoText}>{message}</Text>
    </View>
  )
}

/**
 * Komponent puszki pustego stanu (Empty State) wyświetlany, gdy brak danych na liście.
 *
 * @param props.title - Główny tytuł powiadomienia o braku danych.
 * @param props.description - Opcjonalny opis pomocniczy.
 * @param props.actionLabel - Opcjonalna etykieta przycisku akcji.
 * @param props.onAction - Opcjonalny callback przycisku akcji.
 */
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
  infoBox: {
    backgroundColor: colors.surfaceMuted,
    borderRadius: radius.md,
    padding: space.base,
    borderWidth: 1,
    borderColor: colors.border,
  },
  infoText: {
    color: colors.ink,
    fontSize: typography.sm,
    fontWeight: '500',
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
