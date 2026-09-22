/**
 * @file Button.tsx
 * @description Komponent przycisku z obsługą stany ładowania, wariantów kolorystycznych i niedostępności.
 */

import { ActivityIndicator, Pressable, StyleSheet, Text, type PressableProps } from 'react-native'

import { colors, controlSize, radius, space, typography } from '@/theme/tokens'

/** Wariant stylistyczny przycisku. */
type Variant = 'primary' | 'secondary' | 'danger' | 'ghost'

/** Właściwości komponentu {@link Button}. */
interface ButtonProps extends PressableProps {
  /** Etykieta tekstowa wyświetlana na przycisku. */
  title: string
  /** Czy przycisk jest w stanie ładowania (wyświetla wskaźnik akcji). */
  loading?: boolean
  /** Wariant wizualny przycisku. */
  variant?: Variant
}

/**
 * Standardowy przycisk aplikacji PhysioCare wspierający różne warianty kolorystyczne i wskaźnik ładowania.
 *
 * @param props Właściwości przycisku.
 * @returns Element React Native typu Pressable z odpowiednią stylizacją.
 */
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
    minHeight: controlSize,
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
