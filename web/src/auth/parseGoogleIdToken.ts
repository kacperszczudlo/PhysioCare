/** Decode JWT payload without verifying signature (UI prefill only). */

export type GoogleIdTokenClaims = {
  email?: string
  first_name?: string
  last_name?: string
}

function decodeBase64Utf8(base64Str: string): string {
  const binary = atob(base64Str)
  if (typeof TextDecoder !== 'undefined') {
    const bytes = new Uint8Array(binary.length)
    for (let i = 0; i < binary.length; i++) {
      bytes[i] = binary.charCodeAt(i)
    }
    return new TextDecoder('utf-8').decode(bytes)
  }
  try {
    const percentEncoded = binary
      .split('')
      .map((c) => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
      .join('')
    return decodeURIComponent(percentEncoded)
  } catch {
    return binary
  }
}

function decodeJwtPayload(token: string): Record<string, unknown> | null {
  try {
    const part = token.split('.')[1]
    if (!part) {
      return null
    }
    const normalized = part.replace(/-/g, '+').replace(/_/g, '/')
    const padded = normalized.padEnd(normalized.length + ((4 - (normalized.length % 4)) % 4), '=')
    const json = decodeBase64Utf8(padded)
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
