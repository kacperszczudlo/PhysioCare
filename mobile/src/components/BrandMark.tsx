/**
 * @file BrandMark.tsx
 * @description Komponent renderujący logo lub sygnet marki PhysioCare w różnych wariantach i rozmiarach.
 */

import {
  Image,
  StyleSheet,
  Text,
  View,
  type ImageStyle,
  type StyleProp,
  type ViewStyle,
} from 'react-native'

import { colors, space, typography } from '@/theme/tokens'

/**
 * Właściwości komponentu {@link BrandMark}.
 */
type BrandMarkProps = {
  /** Wariant logo (pełny logotyp dla ekranów logowania lub sygnet dla nagłówka). */
  variant?: 'logo' | 'sygnet'
  /** Rozmiar komponentu grafik (sm, md, lg). */
  size?: 'sm' | 'md' | 'lg'
  /** Opcjonalne hasło/podpis pod logo. */
  tagline?: string
  /** Opcjonalne style dla kontenera zewnętrznego. */
  style?: StyleProp<ViewStyle>
}

const LOGO = require('../../assets/brand/logo.png')
const SYGNET = require('../../assets/brand/sygnet.png')

const SIZES = {
  logo: {
    sm: { width: 180, height: 100 },
    md: { width: 240, height: 130 },
    lg: { width: 300, height: 170 },
  },
  sygnet: {
    sm: { width: 48, height: 48 },
    md: { width: 56, height: 56 },
    lg: { width: 72, height: 72 },
  },
} as const

/**
 * Wyświetla znak graficzny marki PhysioCare (wariant pełny lub sygnet) z opcjonalnym podpisem.
 *
 * @param props Właściwości konfiguracji widoku marki.
 * @returns Element React Native prezentujący logo.
 */
export function BrandMark({ variant = 'logo', size = 'md', tagline, style }: BrandMarkProps) {
  const dims = SIZES[variant][size]
  return (
    <View style={[styles.wrap, style]} accessibilityRole="image" accessibilityLabel="PhysioCare">
      <Image
        source={variant === 'logo' ? LOGO : SYGNET}
        style={dims as ImageStyle}
        resizeMode="contain"
      />
      {tagline ? <Text style={styles.tagline}>{tagline}</Text> : null}
    </View>
  )
}

const styles = StyleSheet.create({
  wrap: { alignItems: 'flex-start', gap: space.xs },
  tagline: { fontSize: typography.base, color: colors.muted },
})
