/** Decode JWT payload without verifying signature (UI prefill only). */

export type GoogleIdTokenClaims = {
  email?: string
  first_name?: string
  last_name?: string
}

function decodeJwtPayload(token: string): Record<string, unknown> | null {
  try {
    const part = token.split('.')[1]
    if (!part) {
      return null
    }
    const normalized = part.replace(/-/g, '+').replace(/_/g, '/')
    const padded = normalized.padEnd(normalized.length + ((4 - (normalized.length % 4)) % 4), '=')
    const json = atob(padded)
    return JSON.parse(json) as Record<string, unknown>
  } catch {
    return null
  }
}

/** Extract email / given_name / family_name from a Google ID token for form prefill. */
export function parseGoogleIdTokenClaims(credential: string): GoogleIdTokenClaims {
  const payload = decodeJwtPayload(credential)
  if (!payload) {
    return {}
  }
  return {
    email: typeof payload.email === 'string' ? payload.email : undefined,
    first_name: typeof payload.given_name === 'string' ? payload.given_name : undefined,
    last_name: typeof payload.family_name === 'string' ? payload.family_name : undefined,
  }
}
