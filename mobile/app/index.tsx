/**
 * @file index.tsx
 * @description Główny punkt wejścia routera przekierowujący użytkownika w zależności od stanu uwierzytelnienia.
 */

import { Redirect } from 'expo-router'

import { useAuth } from '@/auth/AuthContext'

/**
 * Komponent przekierowujący: jeśli użytkownik jest zalogowany -> `/(tabs)`, w przeciwnym razie -> `/(auth)/login`.
 *
 * @returns Komponent przekierowania Redirect z Expo Router.
 */
export default function Index() {
  const { isAuthenticated } = useAuth()
  return <Redirect href={isAuthenticated ? '/(tabs)' : '/(auth)/login'} />
}
