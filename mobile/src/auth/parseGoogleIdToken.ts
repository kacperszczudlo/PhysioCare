/**
 * @file parseGoogleIdToken.ts
 * @description Dekodowanie ładunku tokena JWT z Google (ID Token) bez weryfikacji podpisu w celu wstępnego uzupełnienia pól profilowych (imię, nazwisko, e-mail).
 */

/**
 * Dane użytkownika odczytane z roszczeń (claims) tokena tożsamości Google.
 */
export type GoogleIdTokenClaims = {
  /** Adres e-mail konta Google */
  email?: string
  /** Imię z profilu Google (`given_name`) */
  first_name?: string
  /** Nazwisko z profilu Google (`family_name`) */
  last_name?: string
}

/** Dekoduje ciąg znaków zakodowany w Base64 do tekstu w formacie UTF-8 */
function decodeBase64Utf8(base64Str: string): string {
  const binary = globalThis.atob(base64Str)
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

/** Parsuje ładunek (payload) tokena JWT */
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

/**
 * Dekoduje token ID z usługi Google i wyciąga pola `email`, `given_name` oraz `family_name`.
 *
 * @param credential - Surowy token ID z Google.
 * @returns Odczytane roszczenia profilowe (`GoogleIdTokenClaims`).
 */
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
