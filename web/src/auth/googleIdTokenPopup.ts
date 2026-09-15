/**
 * OpenID Connect implicit popup → Google ID token.
 *
 * Google Cloud → OAuth client (Web):
 * - Authorized JavaScript origins: http://localhost:5173
 * - Authorized redirect URIs:     http://localhost:5173
 */
export function requestGoogleIdTokenPopup(clientId: string): Promise<string> {
  const nonce =
    typeof crypto !== 'undefined' && 'randomUUID' in crypto
      ? crypto.randomUUID().replace(/-/g, '')
      : `${Date.now()}${Math.random().toString(36).slice(2)}`

  const redirectUri = window.location.origin
  const params = new URLSearchParams({
    client_id: clientId,
    redirect_uri: redirectUri,
    response_type: 'id_token',
    scope: 'openid email profile',
    nonce,
    prompt: 'select_account',
  })
  const url = `https://accounts.google.com/o/oauth2/v2/auth?${params.toString()}`

  const width = 480
  const height = 640
  const left = Math.max(0, window.screenX + (window.outerWidth - width) / 2)
  const top = Math.max(0, window.screenY + (window.outerHeight - height) / 2)

  const mismatchHint =
    `Dodaj w Google Cloud (klient Web) Authorized redirect URI dokładnie: ${redirectUri} ` +
    `(oraz Authorized JavaScript origins: ${redirectUri}). Zapisz i poczekaj 1-2 min.`

  return new Promise((resolve, reject) => {
    const popup = window.open(
      url,
      'physiocare-google-oauth',
      `width=${width},height=${height},left=${left},top=${top},menubar=no,toolbar=no`,
    )
    if (!popup) {
      reject(
        new Error(
          'Okno Google zostało zablokowane. Zezwól na wyskakujące okna i spróbuj ponownie.',
        ),
      )
      return
    }

    let settled = false
    const finish = (fn: () => void) => {
      if (settled) {
        return
      }
      settled = true
      window.clearInterval(timer)
      window.removeEventListener('message', onMessage)
      fn()
    }

    const onMessage = (event: MessageEvent) => {
      if (event.origin !== window.location.origin) {
        return
      }
      const data = event.data as { type?: string; id_token?: string; error?: string } | null
      if (!data || data.type !== 'physiocare-google-id-token') {
        return
      }
      popup.close()
      if (data.id_token) {
        finish(() => resolve(data.id_token!))
      } else {
        const err = data.error || 'Logowanie Google nie powiodło się.'
        if (/redirect_uri/i.test(err)) {
          console.warn(`PhysioCare Google Auth Debug: ${mismatchHint}`)
        }
        finish(() =>
          reject(
            new Error(
              /redirect_uri/i.test(err)
                ? 'Niepoprawna konfiguracja adresu przekierowania w serwisie Google.'
                : err,
            ),
          ),
        )
      }
    }
    window.addEventListener('message', onMessage)

    const timer = window.setInterval(() => {
      if (popup.closed) {
        finish(() => reject(new Error('Logowanie Google zostało anulowane.')))
        return
      }
      try {
        const href = popup.location.href
        if (!href.startsWith(redirectUri)) {
          return
        }
        const hash = popup.location.hash.startsWith('#')
          ? popup.location.hash.slice(1)
          : popup.location.hash
        const search = popup.location.search.startsWith('?')
          ? popup.location.search.slice(1)
          : popup.location.search
        const payload = new URLSearchParams(hash || search)
        const idToken = payload.get('id_token')
        const error = payload.get('error')
        const errorDesc = payload.get('error_description') || ''
        popup.close()
        if (idToken) {
          finish(() => resolve(idToken))
        } else {
          const detail = errorDesc || error || 'Google nie zwróciło tokenu.'
          if (/redirect_uri/i.test(detail)) {
            console.warn(`PhysioCare Google Auth Debug: ${mismatchHint}`)
          }
          finish(() =>
            reject(
              new Error(
                /redirect_uri/i.test(detail)
                  ? 'Niepoprawna konfiguracja adresu przekierowania w serwisie Google.'
                  : detail,
              ),
            ),
          )
        }
      } catch {
        // Cross-origin until Google redirects back to our origin.
      }
    }, 300)
  })
}
