/**
 * @file offlineStorage.ts
 * @description Bezpieczna, szyfrowana pamięć trwała dla danych trybu offline i kolejki operacji pacjenta.
 * Wykorzystuje szyfrowanie kluczem zarządzanym przez SecureStore (iOS Keychain / Android Keystore)
 * oraz izolowany katalog aplikacji (expo-file-system) z obsługą wygasania (TTL) i wersjonowania danych.
 */

import * as FileSystem from 'expo-file-system'
import * as SecureStore from 'expo-secure-store'
import { Platform } from 'react-native'

const STORAGE_KEY_ALIAS = 'physiocare_cache_encryption_key'
export const DEFAULT_CACHE_TTL_MS = 7 * 24 * 60 * 60 * 1000 // 7 dni

export interface StorageEnvelope<T> {
  _v: number
  _storedAt: number
  _ttlMs?: number
  data: T
}

const memoryStore = new Map<string, string>()
let inMemoryCryptoKey: CryptoKey | null = null
let inMemoryRawKey: string | null = null

function bytesToHex(bytes: Uint8Array): string {
  return Array.from(bytes)
    .map((b) => b.toString(16).padStart(2, '0'))
    .join('')
}

function hexToBytes(hex: string): Uint8Array {
  const bytes = new Uint8Array(hex.length / 2)
  for (let i = 0; i < bytes.length; i++) {
    bytes[i] = parseInt(hex.slice(i * 2, i * 2 + 2), 16)
  }
  return bytes
}

async function getOrCreateKeyString(): Promise<string> {
  if (inMemoryRawKey) {
    return inMemoryRawKey
  }
  let key = await SecureStore.getItemAsync(STORAGE_KEY_ALIAS)
  if (!key) {
    if (!globalThis.crypto?.getRandomValues) {
      throw new Error('Bezpieczne generowanie klucza cache offline jest niedostępne.')
    }
    const rawBytes = new Uint8Array(32)
    globalThis.crypto.getRandomValues(rawBytes)
    key = bytesToHex(rawBytes)
    await SecureStore.setItemAsync(STORAGE_KEY_ALIAS, key)
  }
  inMemoryRawKey = key
  return key
}

async function getSubtleKey(): Promise<CryptoKey | null> {
  if (inMemoryCryptoKey) {
    return inMemoryCryptoKey
  }
  if (!globalThis.crypto?.subtle) {
    return null
  }
  const rawHex = await getOrCreateKeyString()
  const keyBytes = hexToBytes(rawHex)
  const cryptoKey = await globalThis.crypto.subtle.importKey(
    'raw',
    keyBytes as unknown as BufferSource,
    { name: 'AES-GCM' },
    false,
    ['encrypt', 'decrypt'],
  )
  inMemoryCryptoKey = cryptoKey
  return cryptoKey
}

async function encryptData(plainText: string): Promise<string> {
  const subtleKey = await getSubtleKey()
  if (!subtleKey || !globalThis.crypto?.subtle || !globalThis.crypto.getRandomValues) {
    throw new Error('Bezpieczne szyfrowanie cache offline jest niedostępne.')
  }
  const iv = new Uint8Array(12)
  globalThis.crypto.getRandomValues(iv)
  const encoded = new TextEncoder().encode(plainText)
  const cipherBuffer = await globalThis.crypto.subtle.encrypt(
    { name: 'AES-GCM', iv: iv as unknown as BufferSource },
    subtleKey,
    encoded as unknown as BufferSource,
  )
  const cipherBytes = new Uint8Array(cipherBuffer)
  return `enc:gcm:${bytesToHex(iv)}:${bytesToHex(cipherBytes)}`
}

async function decryptData(cipherText: string): Promise<string> {
  if (!cipherText.startsWith('enc:')) {
    throw new Error('Odrzucono nieszyfrowany wpis cache offline.')
  }

  if (cipherText.startsWith('enc:gcm:')) {
    const parts = cipherText.split(':')
    if (parts.length === 4) {
      const iv = hexToBytes(parts[2])
      const cipherBytes = hexToBytes(parts[3])
      const subtleKey = await getSubtleKey()
      if (subtleKey && globalThis.crypto?.subtle) {
        const decryptedBuffer = await globalThis.crypto.subtle.decrypt(
          { name: 'AES-GCM', iv: iv as unknown as BufferSource },
          subtleKey,
          cipherBytes as unknown as BufferSource,
        )
        return new TextDecoder().decode(decryptedBuffer)
      }
    }
  }

  throw new Error('Nieobsługiwany lub nieprawidłowy format szyfrowania cache.')
}

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
 * Zapisuje obiekt w szyfrowanej pamięci podręcznej offline z opcjonalnym czasem wygaśnięcia (TTL).
 *
 * @param key - Unikalny klucz zasobu.
 * @param value - Obiekt do serializacji.
 * @param ttlMs - Czas życia w milisekundach (domyślnie 7 dni; null oznacza brak wygasania np. dla kolejki outbox).
 */
export async function setOfflineItem<T>(
  key: string,
  value: T,
  ttlMs: number | null = DEFAULT_CACHE_TTL_MS,
): Promise<void> {
  const envelope: StorageEnvelope<T> = {
    _v: 1,
    _storedAt: Date.now(),
    ...(ttlMs !== null ? { _ttlMs: ttlMs } : {}),
    data: value,
  }
  const plainText = JSON.stringify(envelope)
  const encrypted = await encryptData(plainText)
  const filePath = getFilePath(key)

  if (!filePath) {
    memoryStore.set(key, encrypted)
    return
  }

  try {
    await ensureCacheDirExists()
    await FileSystem.writeAsStringAsync(filePath, encrypted, {
      encoding: FileSystem.EncodingType.UTF8,
    })
  } catch {
    // Fallback do pamięci w razie problemów z systemem plików
    memoryStore.set(key, encrypted)
  }
}

/**
 * Odczytuje i odszyfrowuje obiekt z pamięci podręcznej offline, sprawdzając ważność TTL.
 *
 * @param key - Klucz zasobu.
 * @returns Zdeserializowany obiekt lub null w przypadku braku, wygaśnięcia TTL lub błędu.
 */
export async function getOfflineItem<T>(key: string): Promise<T | null> {
  const filePath = getFilePath(key)
  let rawContent: string | null = null

  if (!filePath) {
    rawContent = memoryStore.get(key) ?? null
  } else {
    try {
      const info = await FileSystem.getInfoAsync(filePath)
      if (!info.exists) {
        rawContent = memoryStore.get(key) ?? null
      } else {
        rawContent = await FileSystem.readAsStringAsync(filePath, {
          encoding: FileSystem.EncodingType.UTF8,
        })
      }
    } catch {
      rawContent = memoryStore.get(key) ?? null
    }
  }

  if (!rawContent) {
    return null
  }

  try {
    const decrypted = await decryptData(rawContent)
    const parsed = JSON.parse(decrypted) as unknown

    if (parsed && typeof parsed === 'object' && '_v' in parsed && 'data' in parsed) {
      const envelope = parsed as StorageEnvelope<T>
      if (envelope._ttlMs && Date.now() - envelope._storedAt > envelope._ttlMs) {
        // Dane wygasły – automatyczne usunięcie przestarzałego wpisu
        await removeOfflineItem(key)
        return null
      }
      return envelope.data
    }

    // Wsteczna kompatybilność ze starymi wpisami bez envelope
    return parsed as T
  } catch {
    await removeOfflineItem(key)
    return null
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
  inMemoryCryptoKey = null
  inMemoryRawKey = null

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
