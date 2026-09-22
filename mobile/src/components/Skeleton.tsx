/**
 * @file Skeleton.tsx
 * @description Komponenty bloków zastępczych (skeleton screen) z animacją pulsowania dla stanów ładowania danych.
 */

import React, { useEffect, useState } from 'react'
import {
  AccessibilityInfo,
  DimensionValue,
  StyleProp,
  StyleSheet,
  View,
  ViewStyle,
} from 'react-native'
import Animated, {
  useAnimatedStyle,
  useSharedValue,
  withRepeat,
  withSequence,
  withTiming,
} from 'react-native-reanimated'

import { colors, radius, space } from '@/theme/tokens'

/** Właściwości podstawowego elementu zastępczego {@link Skeleton}. */
export interface SkeletonProps {
  /** Szerokość bloku (liczba w pikselach lub procentowy string). */
  width?: DimensionValue
  /** Wysokość bloku. */
  height?: DimensionValue
  /** Promień zaokrąglenia rogów. */
  borderRadius?: number
  /** Czy blok powinien być idealnym kołem. */
  circle?: boolean
  /** Opcjonalne dodatkowe style. */
  style?: StyleProp<ViewStyle>
}

/**
 * Podstawowy blok ładowania z animowanym pulsem nieprzezroczystości (uwzględnia ustawienia Reduce Motion).
 *
 * @param props Właściwości bloku skeleton.
 * @returns Element React Native Reanimated.
 */
export function Skeleton({
  width,
  height = 16,
  borderRadius = radius.sm,
  circle = false,
  style,
}: SkeletonProps) {
  const [reduceMotion, setReduceMotion] = useState(false)
  const opacity = useSharedValue(0.4)

  useEffect(() => {
    let isMounted = true
    AccessibilityInfo.isReduceMotionEnabled().then((enabled) => {
      if (isMounted) setReduceMotion(enabled)
    })

    if (!reduceMotion) {
      opacity.value = withRepeat(
        withSequence(withTiming(0.85, { duration: 800 }), withTiming(0.4, { duration: 800 })),
        -1,
        true,
      )
    }
    return () => {
      isMounted = false
    }
  }, [opacity, reduceMotion])

  const animatedStyle = useAnimatedStyle(() => ({
    opacity: reduceMotion ? 0.5 : opacity.value,
  }))

  const computedRadius = circle ? (typeof height === 'number' ? height / 2 : 9999) : borderRadius

  return (
    <Animated.View
      accessible={false}
      importantForAccessibility="no-hide-descendants"
      style={[
        styles.skeleton,
        {
          width,
          height,
          borderRadius: computedRadius,
        },
        animatedStyle,
        style,
      ]}
    />
  )
}

/**
 * Blok zastępczy symulujący akapit tekstu składający się z wielu linii.
 *
 * @param props Konfiguracja linii tekstu.
 * @returns Element React Native zawierający układ linii skeleton.
 */
export function SkeletonText({
  lines = 3,
  lineHeight = 14,
  gap = space.xs,
  lastLineWidth = '60%',
  style,
}: {
  /** Liczba generowanych linii. */
  lines?: number
  /** Wysokość pojedynczej linii. */
  lineHeight?: number
  /** Odstęp pionowy między liniami. */
  gap?: number
  /** Szerokość ostatniej linii w akapicie. */
  lastLineWidth?: DimensionValue
  /** Style kontenera. */
  style?: StyleProp<ViewStyle>
}) {
  return (
    <View style={[{ gap }, style]} accessible={false}>
      {Array.from({ length: lines }).map((_, idx) => (
        <Skeleton
          key={idx}
          height={lineHeight}
          width={idx === lines - 1 && lines > 1 ? lastLineWidth : '100%'}
        />
      ))}
    </View>
  )
}

/**
 * Okrągły blok zastępczy symulujący awatar użytkownika.
 *
 * @param props Konfiguracja rozmiaru awatara.
 * @returns Element React Native.
 */
export function SkeletonAvatar({
  size = 40,
  style,
}: {
  /** Średnica koła awatara. */
  size?: number
  /** Style kontenera. */
  style?: StyleProp<ViewStyle>
}) {
  return <Skeleton width={size} height={size} circle style={style} />
}

/**
 * Kontener dostępności dla grupy elementów ładowania powiadamiający czytniki ekranu o stanie busy.
 *
 * @param props Konfiguracja dostępności i dzieci.
 * @returns Element React Native typu View z etykietą dostępności.
 */
export function SkeletonWrapper({
  children,
  label = 'Ładowanie zawartości…',
  style,
}: {
  children: React.ReactNode
  label?: string
  style?: StyleProp<ViewStyle>
}) {
  return (
    <View
      style={style}
      accessibilityRole="text"
      accessibilityLabel={label}
      accessibilityState={{ busy: true }}
    >
      {children}
    </View>
  )
}

const styles = StyleSheet.create({
  skeleton: {
    backgroundColor: colors.border,
  },
})
