import { API_BASE_URL } from '@/api/client'
import { rewriteLocalhostToLan } from '@/lib/lanHost'

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
