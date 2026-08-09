import * as SecureStore from 'expo-secure-store'
import { Platform } from 'react-native'

import type { User } from './types'

const ACCESS_KEY = 'physiocare_access'
const REFRESH_KEY = 'physiocare_refresh'
const USER_KEY = 'physiocare_cached_user'

const memory = new Map<string, string>()

/**
 * Native: SecureStore (Keychain / Keystore).
 * Expo web: localStorage — tylko do dev; produkcyjny klient to native build.
 */
async function setItem(key: string, value: string): Promise<void> {
  if (Platform.OS === 'web') {
    memory.set(key, value)
    try {
      localStorage.setItem(key, value)
    } catch {
    }
    return
  }
  await SecureStore.setItemAsync(key, value)
}

async function getItem(key: string): Promise<string | null> {
  if (Platform.OS === 'web') {
    if (memory.has(key)) {
      return memory.get(key) ?? null
    }
    try {
      return localStorage.getItem(key)
    } catch {
      return null
    }
  }
  return SecureStore.getItemAsync(key)
}

async function deleteItem(key: string): Promise<void> {
  if (Platform.OS === 'web') {
    memory.delete(key)
    try {
      localStorage.removeItem(key)
    } catch {
    }
    return
  }
  await SecureStore.deleteItemAsync(key)
}

export const tokenStorage = {
  async getAccess(): Promise<string | null> {
    return getItem(ACCESS_KEY)
  },

  async getRefresh(): Promise<string | null> {
    return getItem(REFRESH_KEY)
  },

  async setTokens(access: string, refresh: string): Promise<void> {
    await setItem(ACCESS_KEY, access)
    await setItem(REFRESH_KEY, refresh)
  },

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

  async setCachedUser(user: User): Promise<void> {
    await setItem(USER_KEY, JSON.stringify(user))
  },

  async clear(): Promise<void> {
    await deleteItem(ACCESS_KEY)
    await deleteItem(REFRESH_KEY)
    await deleteItem(USER_KEY)
  },
}
