import { Redirect, Stack } from 'expo-router'

import { useAuth } from '@/auth/AuthContext'
import { colors } from '@/theme/tokens'

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
