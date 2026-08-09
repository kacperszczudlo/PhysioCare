import { API_BASE_URL } from '@/api/client'

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
