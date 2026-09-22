/**
 * @file ToastItem.tsx
 * @description Komponent pojedynczej kafelki powiadomienia z animacją wejścia/wyjścia oraz obsługą ręcznego zamykania.
 */

import React, { useCallback, useEffect, useRef } from 'react'
import { Animated, Easing, StyleSheet, Text, TouchableOpacity, View } from 'react-native'

import { colors, radius, space, typography } from '@/theme/tokens'
import type { ToastItemData } from './ToastContext'

/** Właściwości komponentu {@link ToastItem}. */
interface ToastItemProps {
  /** Dane pojedynczego powiadomienia. */
  toast: ToastItemData
  /** Callback do usunięcia powiadomienia po id. */
  onClose: (id: string) => void
}

/**
 * Animowana kafelka powiadomienia Toast z opcjonalnym przyciskiem akcji i zamykania.
 *
 * @param props Właściwości komponentu powiadomienia.
 * @returns Element React Native zawierający animowany widok Toast.
 */
export function ToastItem({ toast, onClose }: ToastItemProps) {
  const translateY = useRef(new Animated.Value(-40)).current
  const opacity = useRef(new Animated.Value(0)).current

  const getAccentColor = () => {
    switch (toast.type) {
      case 'success':
        return colors.success
      case 'error':
        return colors.danger
      case 'warning':
        return colors.warning
      case 'info':
      default:
        return colors.primary
    }
  }

  const handleDismiss = useCallback(() => {
    Animated.parallel([
      Animated.timing(translateY, {
        toValue: -30,
        duration: 180,
        useNativeDriver: true,
        easing: Easing.in(Easing.ease),
      }),
      Animated.timing(opacity, {
        toValue: 0,
        duration: 180,
        useNativeDriver: true,
      }),
    ]).start(() => onClose(toast.id))
  }, [opacity, translateY, onClose, toast.id])

  useEffect(() => {
    Animated.parallel([
      Animated.timing(translateY, {
        toValue: 0,
        duration: 250,
        useNativeDriver: true,
        easing: Easing.out(Easing.back(1.2)),
      }),
      Animated.timing(opacity, {
        toValue: 1,
        duration: 220,
        useNativeDriver: true,
      }),
    ]).start()

    if (toast.duration > 0) {
      const timer = setTimeout(() => {
        handleDismiss()
      }, toast.duration)

      return () => clearTimeout(timer)
    }
  }, [toast.duration, handleDismiss, opacity, translateY])

  const accentColor = getAccentColor()

  return (
    <Animated.View
      style={[
        styles.card,
        { borderLeftColor: accentColor },
        { transform: [{ translateY }], opacity },
      ]}
      accessibilityRole={toast.type === 'error' ? 'alert' : 'none'}
    >
      <View style={styles.content}>
        {toast.title ? <Text style={styles.title}>{toast.title}</Text> : null}
        <Text style={styles.message}>{toast.message}</Text>
        {toast.action ? (
          <TouchableOpacity
            style={styles.actionBtn}
            onPress={() => {
              toast.action?.onPress()
              handleDismiss()
            }}
            activeOpacity={0.7}
          >
            <Text style={[styles.actionText, { color: accentColor }]}>{toast.action.label}</Text>
          </TouchableOpacity>
        ) : null}
      </View>

      <TouchableOpacity
        style={styles.closeBtn}
        onPress={handleDismiss}
        accessibilityLabel="Zamknij"
        hitSlop={{ top: 10, bottom: 10, left: 10, right: 10 }}
      >
        <Text style={styles.closeText}>✕</Text>
      </TouchableOpacity>
    </Animated.View>
  )
}

const styles = StyleSheet.create({
  card: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    backgroundColor: colors.surface,
    borderRadius: radius.md,
    paddingVertical: space.md,
    paddingHorizontal: space.base,
    marginBottom: space.sm,
    borderLeftWidth: 4,
    shadowColor: colors.ink,
    shadowOffset: { width: 0, height: 3 },
    shadowOpacity: 0.12,
    shadowRadius: 6,
    elevation: 4,
    borderWidth: 1,
    borderColor: colors.border,
  },
  content: {
    flex: 1,
    paddingRight: space.sm,
  },
  title: {
    fontSize: typography.sm,
    fontWeight: '700',
    color: colors.ink,
    marginBottom: space.xs / 2,
  },
  message: {
    fontSize: typography.sm,
    color: colors.muted,
    lineHeight: 20,
  },
  actionBtn: {
    marginTop: space.xs,
  },
  actionText: {
    fontSize: typography.xs,
    fontWeight: '700',
    textDecorationLine: 'underline',
  },
  closeBtn: {
    padding: space.xs,
  },
  closeText: {
    fontSize: typography.sm,
    color: colors.faint,
    fontWeight: '600',
  },
})
