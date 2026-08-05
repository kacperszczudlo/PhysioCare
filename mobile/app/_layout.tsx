import { Stack } from 'expo-router'
import { StatusBar } from 'expo-status-bar'
import { ActivityIndicator, StyleSheet, View } from 'react-native'

import { AuthProvider, useAuth } from '@/auth/AuthContext'
import { colors } from '@/theme/tokens'

function RootNavigator() {
  const { isLoading } = useAuth()

  if (isLoading) {
    return (
      <View style={styles.boot}>
        <ActivityIndicator size="large" color={colors.primary} />
      </View>
    )
  }

  return (
    <>
      <StatusBar style="dark" />
      <Stack screenOptions={{ headerShown: false, contentStyle: { backgroundColor: colors.bg } }}>
        <Stack.Screen name="index" />
        <Stack.Screen name="(auth)" />
        <Stack.Screen name="(tabs)" />
        <Stack.Screen
          name="visit/[id]"
          options={{ headerShown: true, title: 'Szczegóły wizyty', presentation: 'card' }}
        />
        <Stack.Screen
          name="therapist/[id]"
          options={{ headerShown: true, title: 'Twój terapeuta', presentation: 'card' }}
        />
      </Stack>
    </>
  )
}

export default function RootLayout() {
  return (
    <AuthProvider>
      <RootNavigator />
    </AuthProvider>
  )
}

const styles = StyleSheet.create({
  boot: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: colors.bg,
  },
})
