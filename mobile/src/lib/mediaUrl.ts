/**
 * @file mediaUrl.ts
 * @description Moduł pomocniczy do budowania pełnych i bezwzględnych adresów URL plików medialnych i obrazów.
 */

import { API_BASE_URL } from '@/api/client'
import { rewriteLocalhostToLan } from '@/lib/lanHost'

/**
 * Przekształca względną ścieżkę pliku multimedialnego z serwera na bezwzględny adres URL (uwzględniający domenę API oraz sieć LAN).
 *
 * @param path - Względna lub pełna ścieżka pliku (np. '/media/avatars/1.jpg').
 * @returns Pełny adres URL pliku lub null, jeśli ścieżka jest pusta.
 */
export function resolveMediaUrl(path: string | null | undefined): string | null {
  if (!path) {
    return null
  }
  if (/^https?:\/\//i.test(path)) {
    return rewriteLocalhostToLan(path)
  }
  const origin = API_BASE_URL.replace(/\/api\/v1\/?$/, '')
  if (path.startsWith('/')) {
    return `${origin}${path}`
  }
  return `${origin}/${path}`
}
