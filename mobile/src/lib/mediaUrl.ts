import { API_BASE_URL } from '@/api/client'

/** Turn `/media/...` from API into a loadable URL for RN Image. */
export function resolveMediaUrl(path: string | null | undefined): string | null {
  if (!path) {
    return null
  }
  if (/^https?:\/\//i.test(path)) {
    return path
  }
  const origin = API_BASE_URL.replace(/\/api\/v1\/?$/, '')
  if (path.startsWith('/')) {
    return `${origin}${path}`
  }
  return `${origin}/${path}`
}
