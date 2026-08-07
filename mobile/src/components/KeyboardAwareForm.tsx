import type { ReactNode } from 'react'
import { StyleSheet, type StyleProp, type ViewStyle } from 'react-native'
import {
  KeyboardAwareScrollView,
  type KeyboardAwareScrollViewProps,
} from 'react-native-keyboard-controller'

type Props = {
  children: ReactNode
  contentContainerStyle?: StyleProp<ViewStyle>
  style?: StyleProp<ViewStyle>
  /** Distance between focused input and keyboard (and tab bar if present). */
  bottomOffset?: number
} & Pick<KeyboardAwareScrollViewProps, 'refreshControl' | 'showsVerticalScrollIndicator'>

/**
 * Form scroll container that keeps the focused TextInput visible above the keyboard.
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
