import { API_BASE_URL } from '@/api/client'

/**
 * Przekształca względną ścieżkę pliku multimedialnego (avatar, film wideo, załącznik) na bezwzględny URL.
 *
 * @param path - Względna lub bezwzględna ścieżka pliku mediów z backendu.
 * @returns Pełny adres URL lub null, jeśli ścieżka była pusta.
 *
 * @example
 * const fullUrl = resolveMediaUrl('/media/avatars/user123.jpg');
 */
export function resolveMediaUrl(path: string | null | undefined): string | null {
  if (!path) {
    return null
  }
  if (/^https?:\/\//i.test(path)) {
    return path
  }
  if (path.startsWith('/')) {
    if (API_BASE_URL.startsWith('http')) {
      const origin = API_BASE_URL.replace(/\/api\/v1\/?$/, '')
      return `${origin}${path}`
    }
    return path
  }
  return path
}
