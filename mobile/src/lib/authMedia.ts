import { useEffect, useState } from 'react'

import { API_BASE_URL } from '@/api/client'
import { tokenStorage } from '@/api/tokenStorage'
import { rewriteLocalhostToLan } from '@/lib/lanHost'
import { resolveMediaUrl } from '@/lib/mediaUrl'

export type AuthenticatedMediaSource = {
  uri: string
  headers?: Record<string, string>
}

/**
 * Build a media source that sends Bearer JWT (required - /media is auth-gated).
 * Suitable for expo-video. For Image / PDF use downloadAuthenticatedMediaToCache
 * or useAuthenticatedCachedUri - RN Image often ignores custom headers.
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

function filenameFromPath(path: string, fallback: string): string {
  const cleaned = path.split('?')[0] ?? path
  const base = cleaned.split('/').pop()
  if (base && base.includes('.')) {
    return base
  }
  return fallback
}

/**
 * Download an auth-protected file to the device cache and return a local file:// URI.
 * Prefer this for RN Image - native image loaders frequently drop Authorization headers.
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
 * Download auth-gated media to a local file:// URI for RN Image (and similar).
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
