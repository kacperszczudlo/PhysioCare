/**
 * @file _layout.tsx
 * @description Nawigator grupy ekranów autoryzacji (logowanie, rejestracja, odzyskiwanie hasła) przekierowujący zalogowanych użytkowników.
 */

import { Redirect, Stack } from 'expo-router'

import { useAuth } from '@/auth/AuthContext'
import { colors } from '@/theme/tokens'

/**
 * Układ ekranów autoryzacji automatycznie przekierowujący uwierzytelnionego użytkownika do głównej części aplikacji `/(tabs)`.
 *
 * @returns Element React Native typu Stack lub komponent przekierowania Redirect.
 */
export default function AuthLayout() {
  const { isAuthenticated } = useAuth()

  if (isAuthenticated) {
    return <Redirect href="/(tabs)" />
  }

  return (
    <Stack
      screenOptions={{
        headerShown: false,
        contentStyle: { backgroundColor: colors.bg },
      }}
    />
  )
}
