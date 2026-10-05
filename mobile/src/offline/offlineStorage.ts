/**
 * @file offlineStorage.ts
 * @description Pamięć trwała dla danych trybu offline i kolejki operacji pacjenta.
 * Wykorzystuje izolowany katalog aplikacji (expo-file-system) na urządzeniach mobilnych
 * oraz localStorage / pamięć RAM na platformie web i w testach jednostkowych.
 */

import * as FileSystem from 'expo-file-system'
import { Platform } from 'react-native'

const memoryStore = new Map<string, string>()

function getCacheDir(): string | null {
  if (Platform.OS === 'web' || !FileSystem.documentDirectory) {
    return null
  }
  return `${FileSystem.documentDirectory}offline_cache/`
}

async function ensureCacheDirExists(): Promise<string | null> {
  const dir = getCacheDir()
  if (!dir) {
    return null
  }
  try {
    const info = await FileSystem.getInfoAsync(dir)
    if (!info.exists) {
      await FileSystem.makeDirectoryAsync(dir, { intermediates: true })
    }
    return dir
  } catch {
    return null
  }
}

function getFilePath(key: string): string | null {
  const dir = getCacheDir()
  if (!dir) {
    return null
  }
  const safeKey = key.replace(/[^a-zA-Z0-9_-]/g, '_')
  return `${dir}${safeKey}.json`
}

/**
 * Zapisuje obiekt w trwałej pamięci podręcznej offline.
 *
 * @param key - Unikalny klucz zasobu.
 * @param value - Obiekt do serializacji JSON.
 */
export async function setOfflineItem<T>(key: string, value: T): Promise<void> {
  const raw = JSON.stringify(value)
  const filePath = getFilePath(key)

  if (!filePath) {
    memoryStore.set(key, raw)
    if (typeof localStorage !== 'undefined') {
      try {
        localStorage.setItem(`physiocare_offline_${key}`, raw)
      } catch {}
    }
    return
  }

  try {
    await ensureCacheDirExists()
    await FileSystem.writeAsStringAsync(filePath, raw, {
      encoding: FileSystem.EncodingType.UTF8,
    })
  } catch {
    // Fallback do pamięci w razie problemów z systemem plików
    memoryStore.set(key, raw)
  }
}

/**
 * Odczytuje obiekt z trwałej pamięci podręcznej offline.
 *
 * @param key - Klucz zasobu.
 * @returns Zdeserializowany obiekt lub null w przypadku braku lub błędu.
 */
export async function getOfflineItem<T>(key: string): Promise<T | null> {
  const filePath = getFilePath(key)

  if (!filePath) {
    const inMem = memoryStore.get(key)
    if (inMem) {
      try {
        return JSON.parse(inMem) as T
      } catch {
        return null
      }
    }
    if (typeof localStorage !== 'undefined') {
      try {
        const raw = localStorage.getItem(`physiocare_offline_${key}`)
        return raw ? (JSON.parse(raw) as T) : null
      } catch {
        return null
      }
    }
    return null
  }

  try {
    const info = await FileSystem.getInfoAsync(filePath)
    if (!info.exists) {
      // Sprawdź czy jest w pamięci tymczasowej
      const inMem = memoryStore.get(key)
      return inMem ? (JSON.parse(inMem) as T) : null
    }
    const content = await FileSystem.readAsStringAsync(filePath, {
      encoding: FileSystem.EncodingType.UTF8,
    })
    return JSON.parse(content) as T
  } catch {
    const inMem = memoryStore.get(key)
    return inMem ? (JSON.parse(inMem) as T) : null
  }
}

/**
 * Usuwa konkretny zasób z pamięci podręcznej offline.
 *
 * @param key - Klucz do usunięcia.
 */
export async function removeOfflineItem(key: string): Promise<void> {
  memoryStore.delete(key)
  if (typeof localStorage !== 'undefined') {
    try {
      localStorage.removeItem(`physiocare_offline_${key}`)
    } catch {}
  }

  const filePath = getFilePath(key)
  if (filePath) {
    try {
      const info = await FileSystem.getInfoAsync(filePath)
      if (info.exists) {
        await FileSystem.deleteAsync(filePath, { idempotent: true })
      }
    } catch {}
  }
}

/**
 * Czyści wszystkie dane pamięci podręcznej offline (wywoływane przy wylogowaniu).
 */
export async function clearAllOfflineData(): Promise<void> {
  memoryStore.clear()
  if (typeof localStorage !== 'undefined') {
    try {
      const toRemove: string[] = []
      for (let i = 0; i < localStorage.length; i++) {
        const k = localStorage.key(i)
        if (k?.startsWith('physiocare_offline_')) {
          toRemove.push(k)
        }
      }
      toRemove.forEach((k) => localStorage.removeItem(k))
    } catch {}
  }

  const dir = getCacheDir()
  if (dir) {
    try {
      const info = await FileSystem.getInfoAsync(dir)
      if (info.exists) {
        await FileSystem.deleteAsync(dir, { idempotent: true })
      }
    } catch {}
  }
}
