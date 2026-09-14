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

export interface SkeletonProps {
  width?: DimensionValue
  height?: DimensionValue
  borderRadius?: number
  circle?: boolean
  style?: StyleProp<ViewStyle>
}

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

export function SkeletonText({
  lines = 3,
  lineHeight = 14,
  gap = space.xs,
  lastLineWidth = '60%',
  style,
}: {
  lines?: number
  lineHeight?: number
  gap?: number
  lastLineWidth?: DimensionValue
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

export function SkeletonAvatar({
  size = 40,
  style,
}: {
  size?: number
  style?: StyleProp<ViewStyle>
}) {
  return <Skeleton width={size} height={size} circle style={style} />
}

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
