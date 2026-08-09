import { Ionicons } from '@expo/vector-icons'
import { useState } from 'react'
import {
  Pressable,
  StyleSheet,
  Text,
  TextInput,
  View,
  type TextInputProps,
} from 'react-native'

import { colors, controlSize, iconSize, radius, space, typography } from '@/theme/tokens'

interface FieldProps extends TextInputProps {
  label: string
  error?: string | null
  hint?: string
  /** When secureTextEntry is set, show a reveal toggle (default true). */
  revealable?: boolean
}

export function Field({
  label,
  error,
  hint,
  style,
  secureTextEntry,
  revealable,
  ...rest
}: FieldProps) {
  const [revealed, setRevealed] = useState(false)
  const canReveal = Boolean(secureTextEntry) && (revealable ?? true)
  const isSecure = Boolean(secureTextEntry) && !(canReveal && revealed)

  return (
    <View style={styles.wrap}>
      <Text style={styles.label}>{label}</Text>
      <View style={styles.control}>
        <TextInput
          {...rest}
          placeholderTextColor={colors.faint}
          style={[
            styles.input,
            canReveal ? styles.inputWithReveal : null,
            error ? styles.inputError : null,
            style,
          ]}
          secureTextEntry={isSecure}
        />
        {canReveal ? (
          <Pressable
            accessibilityRole="button"
            accessibilityLabel={revealed ? 'Ukryj hasło' : 'Pokaż hasło'}
            accessibilityState={{ selected: revealed }}
            hitSlop={8}
            onPress={() => setRevealed((prev) => !prev)}
            style={({ pressed }) => [styles.reveal, pressed ? styles.revealPressed : null]}
          >
            <Ionicons
              name={revealed ? 'eye-off-outline' : 'eye-outline'}
              size={iconSize.lg}
              color={colors.muted}
            />
          </Pressable>
        ) : null}
      </View>
      {error ? (
        <Text style={styles.error} accessibilityLiveRegion="polite">
          {error}
        </Text>
      ) : hint ? (
        <Text style={styles.hint}>{hint}</Text>
      ) : null}
    </View>
  )
}

const styles = StyleSheet.create({
  wrap: {
    gap: space.sm,
  },
  label: {
    fontSize: typography.sm,
    fontWeight: '600',
    color: colors.ink,
  },
  control: {
    position: 'relative',
    justifyContent: 'center',
  },
  input: {
    minHeight: controlSize,
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: radius.md,
    paddingHorizontal: space.base,
    paddingVertical: space.md,
    fontSize: typography.base,
    color: colors.ink,
    backgroundColor: colors.surface,
  },
  inputWithReveal: {
    paddingRight: controlSize,
  },
  inputError: {
    borderColor: colors.danger,
  },
  reveal: {
    position: 'absolute',
    right: 0,
    top: 0,
    bottom: 0,
    width: controlSize,
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: radius.sm,
  },
  revealPressed: {
    backgroundColor: colors.surfaceMuted,
  },
  error: {
    fontSize: typography.sm,
    color: colors.danger,
  },
  hint: {
    fontSize: typography.sm,
    color: colors.muted,
  },
})
