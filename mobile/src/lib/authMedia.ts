/**
 * @file authMedia.ts
 * @description Plik pomocniczy do obsługi chronionych zasobów multimedialnych (obrazy, filmy, PDF) wymagających nagłówka autoryzacyjnego Bearer JWT.
 */

import { useEffect, useState } from 'react'

import { API_BASE_URL } from '@/api/client'
import { tokenStorage } from '@/api/tokenStorage'
import { rewriteLocalhostToLan } from '@/lib/lanHost'
import { resolveMediaUrl } from '@/lib/mediaUrl'

/**
 * Struktura źródła pliku multimedialnego z dołączonymi nagłówkami autoryzacji HTTP.
 */
export type AuthenticatedMediaSource = {
  /** Adres URL pliku multimedialnego */
  uri: string
  /** Nagłówki HTTP (w tym Authorization Bearer) */
  headers?: Record<string, string>
}

/**
 * Buduje obiekt źródła multimediów zawierający token Bearer JWT.
 * Przydatne dla komponentów obsługujących nagłówki (np. `expo-video`).
 *
 * @param path - Względna lub bezwzględna ścieżka do pliku multimedialnego.
 * @returns Zwraca obietnicę z obiektem `AuthenticatedMediaSource` lub `null`.
 */
export async function getAuthenticatedMediaSource(
  path: string | null | undefined,
): Promise<AuthenticatedMediaSource | null> {
  const uri = resolveMediaUrl(path)
  if (!uri) {
    return null
  }

  const access = await tokenStorage.getAccess()
  if (!access) {
    return null
  }

  return {
    uri,
    headers: { Authorization: `Bearer ${access}` },
  }
}

/** Tworzy bezwzględny URL z uwzględnieniem mapowania hosta LAN */
function mediaAbsoluteUrl(path: string): string {
  if (/^https?:\/\//i.test(path)) {
    return rewriteLocalhostToLan(path)
  }
  if (path.startsWith('/api/')) {
    const origin = API_BASE_URL.replace(/\/api\/v1\/?$/, '')
    return `${origin}${path}`
  }
  return resolveMediaUrl(path) ?? path
}

/** Wyciąga bezpieczną nazwę pliku z podanej ścieżki */
function filenameFromPath(path: string, fallback: string): string {
  const cleaned = path.split('?')[0] ?? path
  const base = cleaned.split('/').pop()
  if (base && base.includes('.')) {
    return base
  }
  return fallback
}

/**
 * Pobiera chroniony plik ze stosowaniem tokenu JWT i zapisuje go w pamięci podręcznej urządzenia (cache), zwracając lokalny URI file://.
 * Zalecane rozwiązanie dla komponentu React Native Image, który nie zawsze poprawnie przekazuje nagłówki HTTP na poziomie natywnym.
 *
 * @param path - Ścieżka pliku z serwera.
 * @param filenameHint - Opcjonalny wariant nazwy pliku (domyślnie 'document.pdf').
 * @returns Zwraca obietnicę z lokalnym adresem file:// lub null w przypadku niepowodzenia.
 */
export async function downloadAuthenticatedMediaToCache(
  path: string | null | undefined,
  filenameHint = 'document.pdf',
): Promise<string | null> {
  if (!path) {
    return null
  }

  const access = await tokenStorage.getAccess()
  if (!access) {
    return null
  }

  const url = mediaAbsoluteUrl(path)
  const FileSystem = await import('expo-file-system')
  const cacheDir = FileSystem.cacheDirectory
  if (!cacheDir) {
    return null
  }
  const safeName = filenameFromPath(path, filenameHint).replace(/[^a-zA-Z0-9._-]/g, '_')
  const target = `${cacheDir}${Date.now()}-${safeName}`

  const result = await FileSystem.downloadAsync(url, target, {
    headers: { Authorization: `Bearer ${access}` },
  })

  if (result.status !== 200) {
    return null
  }
  return result.uri
}

/**
 * Hook React do asynchronicznego pobierania autoryzowanego źródła multimediów.
 *
 * @param path - Ścieżka do chronionego pliku.
 * @returns Obiekt ze stanem źródła, wskaźnikiem ładowania i błędu.
 */
export function useAuthenticatedMediaSource(path: string | null | undefined): {
  source: AuthenticatedMediaSource | null
  loading: boolean
  error: boolean
} {
  const [source, setSource] = useState<AuthenticatedMediaSource | null>(null)
  const [loading, setLoading] = useState(Boolean(path))
  const [error, setError] = useState(false)

  useEffect(() => {
    let cancelled = false

    if (!path) {
      setSource(null)
      setLoading(false)
      setError(false)
      return
    }

    setLoading(true)
    setError(false)

    void getAuthenticatedMediaSource(path)
      .then((next) => {
        if (cancelled) {
          return
        }
        setSource(next)
        setError(!next)
      })
      .catch(() => {
        if (!cancelled) {
          setSource(null)
          setError(true)
        }
      })
      .finally(() => {
        if (!cancelled) {
          setLoading(false)
        }
      })

    return () => {
      cancelled = true
    }
  }, [path])

  return { source, loading, error }
}

/**
 * Hook React pobierający i keszujący chroniony plik na urządzeniu w lokalnym pliku file://.
 *
 * @param path - Ścieżka pliku z serwera API.
 * @returns Obiekt zawierający lokalny adres `uri`, status ładowania oraz stan błędu.
 */
export function useAuthenticatedCachedUri(path: string | null | undefined): {
  uri: string | null
  loading: boolean
  error: boolean
} {
  const [uri, setUri] = useState<string | null>(null)
  const [loading, setLoading] = useState(Boolean(path))
  const [error, setError] = useState(false)

  useEffect(() => {
    let cancelled = false

    if (!path) {
      setUri(null)
      setLoading(false)
      setError(false)
      return
    }

    setLoading(true)
    setError(false)
    setUri(null)

    void downloadAuthenticatedMediaToCache(path, 'avatar.jpg')
      .then((localUri) => {
        if (cancelled) {
          return
        }
        setUri(localUri)
        setError(!localUri)
      })
      .catch(() => {
        if (!cancelled) {
          setUri(null)
          setError(true)
        }
      })
      .finally(() => {
        if (!cancelled) {
          setLoading(false)
        }
      })

    return () => {
      cancelled = true
    }
  }, [path])

  return { uri, loading, error }
}

