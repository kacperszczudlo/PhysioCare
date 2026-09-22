/**
 * @file GoogleMark.tsx
 * @description Komponent ikony logo Google wykorzystywany w przyciskach logowania SSO.
 */

import { Image, type ImageStyle, type StyleProp } from 'react-native'

/** Właściwości komponentu {@link GoogleMark}. */
type GoogleMarkProps = {
  /** Rozmiar ikony w pikselach (szerokość i wysokość, domyślnie 20). */
  size?: number
  /** Opcjonalne style grafiki. */
  style?: StyleProp<ImageStyle>
}

/**
 * Wyświetla grafikę z oficjalnym logo Google.
 *
 * @param props Właściwości ikony Google.
 * @returns Element React Native typu Image.
 */
export function GoogleMark({ size = 20, style }: GoogleMarkProps) {
  return (
    <Image
      accessibilityIgnoresInvertColors
      source={require('../../assets/google-logo.png')}
      style={[{ width: size, height: size }, style]}
      resizeMode="contain"
    />
  )
}
