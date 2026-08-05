import { ActivityIndicator, Pressable, StyleSheet, Text, type PressableProps } from 'react-native'

import { colors, radius, space, typography } from '@/theme/tokens'

type Variant = 'primary' | 'secondary' | 'danger' | 'ghost'

interface ButtonProps extends PressableProps {
  title: string
  loading?: boolean
  variant?: Variant
}

export function Button({
  title,
  loading = false,
  variant = 'primary',
  disabled,
  style,
  ...rest
}: ButtonProps) {
  const isDisabled = disabled || loading

  return (
    <Pressable
      accessibilityRole="button"
      disabled={isDisabled}
      style={(state) => [
        styles.base,
        styles[variant],
        state.pressed && !isDisabled ? styles.pressed : null,
        isDisabled ? styles.disabled : null,
        typeof style === 'function' ? style(state) : style,
      ]}
      {...rest}
    >
      {loading ? (
        <ActivityIndicator
          color={variant === 'primary' || variant === 'danger' ? colors.onPrimary : colors.primary}
        />
      ) : (
        <Text style={[styles.label, styles[`label_${variant}`]]}>{title}</Text>
      )}
    </Pressable>
  )
}

const styles = StyleSheet.create({
  base: {
    minHeight: 48,
    borderRadius: radius.md,
    paddingHorizontal: space.lg,
    alignItems: 'center',
    justifyContent: 'center',
  },
  primary: {
    backgroundColor: colors.primary,
  },
  secondary: {
    backgroundColor: colors.primarySubtle,
    borderWidth: 1,
    borderColor: colors.border,
  },
  danger: {
    backgroundColor: colors.danger,
  },
  ghost: {
    backgroundColor: 'transparent',
  },
  pressed: {
    opacity: 0.88,
  },
  disabled: {
    opacity: 0.5,
  },
  label: {
    fontSize: typography.base,
    fontWeight: '600',
  },
  label_primary: {
    color: colors.onPrimary,
  },
  label_secondary: {
    color: colors.primary,
  },
  label_danger: {
    color: colors.onPrimary,
  },
  label_ghost: {
    color: colors.primary,
  },
})
