/**
 * @file _layout.tsx
 * @description Główny (korzenny) nawigator aplikacji PhysioCare ze wszystkimi dostawcami kontekstów (Auth, Network, Toast, Realtime).
 */

import 'react-native-reanimated'
import { Stack } from 'expo-router'
import { StatusBar } from 'expo-status-bar'
import { ActivityIndicator, StyleSheet, View } from 'react-native'
import { KeyboardProvider } from 'react-native-keyboard-controller'
import { SafeAreaProvider } from 'react-native-safe-area-context'

import { AuthProvider, useAuth } from '@/auth/AuthContext'
import { BrandMark } from '@/components/BrandMark'
import { OfflineBanner } from '@/components/OfflineBanner'
import { OfflineSyncObserver } from '@/offline/OfflineSyncObserver'
import { configureNotificationHandler } from '@/notifications/push'
import { NotificationObserver } from '@/notifications/NotificationObserver'
import { RealtimeObserver } from '@/realtime/RealtimeObserver'
import { colors, space } from '@/theme/tokens'
import { NetworkProvider } from '@/network/NetworkContext'
import { ToastContainer } from '@/components/ToastContainer'
import { ToastProvider } from '@/components/ToastContext'

configureNotificationHandler()

/**
 * Wewnętrzny nawigator stosu (Stack) zarządcy ekranów po załadowaniu kontekstu uwierzytelniania.
 *
 * @returns Element React Native prezentujący ekrany aplikacji lub ekran ładowania.
 */
function RootNavigator() {
  const { isLoading } = useAuth()

  if (isLoading) {
    return (
      <View style={styles.shell}>
        <OfflineBanner />
        <View style={styles.boot}>
          <BrandMark variant="logo" size="lg" style={styles.bootBrand} />
          <ActivityIndicator size="large" color={colors.primary} style={styles.bootSpinner} />
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
          <Stack.Screen name="password-reset" options={{ headerShown: false }} />
          <Stack.Screen
            name="visit/[id]"
            options={{ headerShown: true, title: 'Szczegóły wizyty', presentation: 'card' }}
          />
          <Stack.Screen
            name="visit/request"
            options={{ headerShown: true, title: 'Umów wizytę', presentation: 'card' }}
          />
          <Stack.Screen
            name="exercise/[id]"
            options={{ headerShown: true, title: 'Ćwiczenie', presentation: 'card' }}
          />
          <Stack.Screen
            name="therapist/[id]"
            options={{ headerShown: true, title: 'Twój terapeuta', presentation: 'card' }}
          />
          <Stack.Screen name="legal/privacy" options={{ headerShown: true, title: 'Prywatność' }} />
          <Stack.Screen name="legal/cookies" options={{ headerShown: true, title: 'Cookies' }} />
          <Stack.Screen
            name="legal/account-deletion"
            options={{ headerShown: true, title: 'Usuwanie konta' }}
          />
        </Stack>
      </View>
    </View>
  )
}

/**
 * Korzenny komponent układu aplikacji (Root Layout) owijający całe drzewo w dostawców powiadomień, sieci i autoryzacji.
 *
 * @returns Główny element układu aplikacji.
 */
export default function RootLayout() {
  return (
    <SafeAreaProvider>
      <KeyboardProvider preload={false}>
        <ToastProvider>
          <NetworkProvider>
            <AuthProvider>
              <NotificationObserver />
              <RealtimeObserver />
              <OfflineSyncObserver />
              <RootNavigator />
              <ToastContainer />
            </AuthProvider>
          </NetworkProvider>
        </ToastProvider>
      </KeyboardProvider>
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
    gap: space.lg,
  },
  bootBrand: {
    alignItems: 'center',
  },
  bootSpinner: {
    marginTop: space.xs,
  },
})
