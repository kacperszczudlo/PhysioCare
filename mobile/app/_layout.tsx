import { Stack } from 'expo-router'
import { StatusBar } from 'expo-status-bar'
import { ActivityIndicator, StyleSheet, View } from 'react-native'
import { SafeAreaProvider } from 'react-native-safe-area-context'

import { AuthProvider, useAuth } from '@/auth/AuthContext'
import { OfflineBanner } from '@/components/OfflineBanner'
import { NetworkProvider } from '@/network/NetworkContext'
import { colors } from '@/theme/tokens'

function RootNavigator() {
  const { isLoading } = useAuth()

  if (isLoading) {
    return (
      <View style={styles.shell}>
        <OfflineBanner />
        <View style={styles.boot}>
          <ActivityIndicator size="large" color={colors.primary} />
        </View>
      </View>
    )
  }

  return (
    <View style={styles.shell}>
      <StatusBar style="dark" />
      <OfflineBanner />
      <View style={styles.flex}>
        <Stack screenOptions={{ headerShown: false, contentStyle: { backgroundColor: colors.bg } }}>
          <Stack.Screen name="index" />
          <Stack.Screen name="(auth)" />
          <Stack.Screen name="(tabs)" />
          <Stack.Screen
            name="visit/[id]"
            options={{ headerShown: true, title: 'Szczegóły wizyty', presentation: 'card' }}
          />
          <Stack.Screen
            name="exercise/[id]"
            options={{ headerShown: true, title: 'Ćwiczenie', presentation: 'card' }}
          />
          <Stack.Screen
            name="therapist/[id]"
            options={{ headerShown: true, title: 'Twój terapeuta', presentation: 'card' }}
          />
        </Stack>
      </View>
    </View>
  )
}

export default function RootLayout() {
  return (
    <SafeAreaProvider>
      <NetworkProvider>
        <AuthProvider>
          <RootNavigator />
        </AuthProvider>
      </NetworkProvider>
    </SafeAreaProvider>
  )
}

const styles = StyleSheet.create({
  shell: {
    flex: 1,
    backgroundColor: colors.bg,
  },
  flex: {
    flex: 1,
  },
  boot: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: colors.bg,
  },
})
