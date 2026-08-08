import { useEffect, useState } from 'react'

import { resolveMediaUrl } from '@/lib/mediaUrl'

const objectUrlCache = new Map<string, string>()

/**
 * Fetch a protected /media/... (or API download) URL with session cookies
 * and return a blob: object URL suitable for <img>, <video>, and window.open.
 */
export async function fetchAuthenticatedMediaObjectUrl(
  path: string | null | undefined,
): Promise<string | null> {
  const resolved = resolveMediaUrl(path)
  if (!resolved) {
    return null
  }

  const cached = objectUrlCache.get(resolved)
  if (cached) {
    return cached
  }

  const response = await fetch(resolved, {
    method: 'GET',
    credentials: 'include',
    headers: { Accept: '*/*' },
  })

  if (!response.ok) {
    return null
  }

  const blob = await response.blob()
  const objectUrl = URL.createObjectURL(blob)
  objectUrlCache.set(resolved, objectUrl)
  return objectUrl
}

export function useAuthenticatedMediaUrl(path: string | null | undefined): {
  url: string | null
  loading: boolean
  error: boolean
} {
  const [url, setUrl] = useState<string | null>(null)
  const [loading, setLoading] = useState(Boolean(path))
  const [error, setError] = useState(false)

  useEffect(() => {
    let cancelled = false

    if (!path) {
      setUrl(null)
      setLoading(false)
      setError(false)
      return
    }

    setLoading(true)
    setError(false)

    void fetchAuthenticatedMediaObjectUrl(path)
      .then((objectUrl) => {
        if (cancelled) {
          return
        }
        setUrl(objectUrl)
        setError(!objectUrl)
      })
      .catch(() => {
        if (!cancelled) {
          setUrl(null)
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

  return { url, loading, error }
}
