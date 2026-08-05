import { StyleSheet, Text, TextInput, View, type TextInputProps } from 'react-native'

import { colors, radius, space, typography } from '@/theme/tokens'

interface FieldProps extends TextInputProps {
  label: string
  error?: string | null
  hint?: string
}

export function Field({ label, error, hint, style, ...rest }: FieldProps) {
  return (
    <View style={styles.wrap}>
      <Text style={styles.label}>{label}</Text>
      <TextInput
        placeholderTextColor={colors.faint}
        style={[styles.input, error ? styles.inputError : null, style]}
        {...rest}
      />
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
  input: {
    minHeight: 48,
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: radius.md,
    paddingHorizontal: space.base,
    paddingVertical: space.md,
    fontSize: typography.base,
    color: colors.ink,
    backgroundColor: colors.surface,
  },
  inputError: {
    borderColor: colors.danger,
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
