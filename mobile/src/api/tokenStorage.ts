/**
 * @file tokenStorage.ts
 * @description Bezpieczny magazyn tokenów autoryzacyjnych JWT (SecureStore na iOS/Android, pamięć/localStorage w przeglądarce).
 */

import * as SecureStore from 'expo-secure-store'
import { Platform } from 'react-native'

import type { User } from './types'

const ACCESS_KEY = 'physiocare_access'
const REFRESH_KEY = 'physiocare_refresh'
const USER_KEY = 'physiocare_cached_user'
const PUSH_TOKEN_KEY = 'physiocare_expo_push_token'

const memory = new Map<string, string>()

/**
 * Zapisuje klucz i wartość w bezpiecznym magazynie urządzeń mobilnych (Keychain/Keystore) lub pamięci web.
 *
 * @param key - Klucz wpisu.
 * @param value - Wartość tekstowa.
 */
async function setItem(key: string, value: string): Promise<void> {
  if (Platform.OS === 'web') {
    memory.set(key, value)
    return
  }
  await SecureStore.setItemAsync(key, value)
}

/**
 * Pobiera wartość wpisu na podstawie klucza.
 *
 * @param key - Klucz wpisu.
 * @returns Wartość tekstowa lub null w przypadku braku wpisu.
 */
async function getItem(key: string): Promise<string | null> {
  if (Platform.OS === 'web') {
    return memory.get(key) ?? null
  }
  return SecureStore.getItemAsync(key)
}

/**
 * Usuwa dany wpis z magazynu.
 *
 * @param key - Klucz do usunięcia.
 */
async function deleteItem(key: string): Promise<void> {
  if (Platform.OS === 'web') {
    memory.delete(key)
    try {
      if (typeof localStorage !== 'undefined') {
        localStorage.removeItem(key)
      }
    } catch {}
    return
  }
  await SecureStore.deleteItemAsync(key)
}

/**
 * Obiekt zarządzający magazynem tokenów sesji oraz podręcznym cashem profilu użytkownika.
 */
export const tokenStorage = {
  /**
   * Pobiera zapisany access token JWT.
   *
   * @returns Access token lub null.
   */
  async getAccess(): Promise<string | null> {
    return getItem(ACCESS_KEY)
  },

  /**
   * Pobiera zapisany refresh token JWT.
   *
   * @returns Refresh token lub null.
   */
  async getRefresh(): Promise<string | null> {
    return getItem(REFRESH_KEY)
  },

  /**
   * Zapisuje nowy zestaw tokenów (access oraz refresh).
   *
   * @param access - Token dostępowy JWT.
   * @param refresh - Token odświeżania JWT.
   */
  async setTokens(access: string, refresh: string): Promise<void> {
    await setItem(ACCESS_KEY, access)
    await setItem(REFRESH_KEY, refresh)
  },

  /**
   * Pobiera podręcznie zapisanego użytkownika (offline cache).
   *
   * @returns Obiekt użytkownika lub null.
   */
  async getCachedUser(): Promise<User | null> {
    const raw = await getItem(USER_KEY)
    if (!raw) {
      return null
    }
    try {
      return JSON.parse(raw) as User
    } catch {
      return null
    }
  },

  /**
   * Zapisuje obiekt użytkownika w podręcznym magazynie.
   *
   * @param user - Obiekt profilu użytkownika.
   */
  async setCachedUser(user: User): Promise<void> {
    await setItem(USER_KEY, JSON.stringify(user))
  },

  /**
   * Pobiera zarejestrowany token push powiadomień Expo.
   *
   * @returns Token powiadomień Push lub null.
   */
  async getPushToken(): Promise<string | null> {
    return getItem(PUSH_TOKEN_KEY)
  },

  /**
   * Zapisuje token push powiadomień urządzenia.
   *
   * @param token - Token powiadomień Expo Push.
   */
  async setPushToken(token: string): Promise<void> {
    await setItem(PUSH_TOKEN_KEY, token)
  },

  /**
   * Usuwa token powiadomień z pamięci urządzenia.
   */
  async clearPushToken(): Promise<void> {
    await deleteItem(PUSH_TOKEN_KEY)
  },

  /**
   * Czyści wszystkie zapamiętane tokeny autoryzacyjne oraz zapisany profil użytkownika.
   */
  async clear(): Promise<void> {
    await deleteItem(ACCESS_KEY)
    await deleteItem(REFRESH_KEY)
    try {
      const { clearOfflineQueue } = await import('@/offline/offlineQueue')
      await clearOfflineQueue()
    } catch {}
    await deleteItem(USER_KEY)
    try {
      const { clearAllOfflineData } = await import('@/offline/offlineStorage')
      await clearAllOfflineData()
    } catch {}
  },
}
