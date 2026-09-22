/**
 * @file KeyboardAwareForm.tsx
 * @description Kontener przewijany dla formularzy dopasowujący układ do pojawiającej się klawiatury na urządzeniach mobilnych.
 */

import type { ReactNode } from 'react'
import { StyleSheet, type StyleProp, type ViewStyle } from 'react-native'
import {
  KeyboardAwareScrollView,
  type KeyboardAwareScrollViewProps,
} from 'react-native-keyboard-controller'

/** Właściwości komponentu {@link KeyboardAwareForm}. */
type Props = {
  /** Zawartość formularza (pola, przyciski). */
  children: ReactNode
  /** Opcjonalne style widoku zawartości przewijanej. */
  contentContainerStyle?: StyleProp<ViewStyle>
  /** Opcjonalne style kontenera głównego. */
  style?: StyleProp<ViewStyle>
  /** Odstęp między aktywnym polem tekstowym a klawiaturą (domyślnie 40). */
  bottomOffset?: number
} & Pick<KeyboardAwareScrollViewProps, 'refreshControl' | 'showsVerticalScrollIndicator'>

/**
 * Kontener scrollable dla formularzy automatycznie przesuwający aktywne pole tekstowe ponad klawiaturę ekranową.
 *
 * @param props Właściwości kontenera formularza.
 * @returns Element React Native bazujący na KeyboardAwareScrollView.
 */
export function KeyboardAwareForm({
  children,
  contentContainerStyle,
  style,
  bottomOffset = 40,
  refreshControl,
  showsVerticalScrollIndicator = false,
}: Props) {
  return (
    <KeyboardAwareScrollView
      style={[styles.flex, style]}
      contentContainerStyle={contentContainerStyle}
      bottomOffset={bottomOffset}
      extraKeyboardSpace={bottomOffset}
      keyboardShouldPersistTaps="handled"
      keyboardDismissMode="interactive"
      showsVerticalScrollIndicator={showsVerticalScrollIndicator}
      refreshControl={refreshControl}
    >
      {children}
    </KeyboardAwareScrollView>
  )
}

const styles = StyleSheet.create({
  flex: { flex: 1 },
})
