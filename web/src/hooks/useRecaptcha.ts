import { useCallback, useEffect, useRef } from 'react'

declare global {
  interface Window {
    grecaptcha?: {
      ready: (callback: () => void) => void
      execute: (siteKey: string, options: { action: string }) => Promise<string>
    }
  }
}

const SITE_KEY = (import.meta.env.VITE_RECAPTCHA_SITE_KEY as string | undefined) || ''
const SCRIPT_LOAD_TIMEOUT_MS = 6000
const RECAPTCHA_READY_TIMEOUT_MS = 5000

/**
 * Hook React ładujący skrypt Google reCAPTCHA v3 oraz udostępniający funkcję wyzwalania tokena weryfikacji.
 *
 * @returns Obiekt zawierający funkcję `executeRecaptcha` oraz flagę `isRecaptchaConfigured`.
 *
 * @example
 * const { executeRecaptcha } = useRecaptcha();
 * const token = await executeRecaptcha('login');
 */
export function useRecaptcha() {
  const scriptFailedRef = useRef(false)

  useEffect(() => {
    if (!SITE_KEY) return

    const scriptId = 'google-recaptcha-script'
    if (document.getElementById(scriptId)) return

    scriptFailedRef.current = false
    const script = document.createElement('script')
    script.id = scriptId
    script.src = `https://www.google.com/recaptcha/api.js?render=${encodeURIComponent(SITE_KEY)}`
    script.async = true
    script.onerror = () => {
      scriptFailedRef.current = true
    }
    document.head.appendChild(script)
  }, [])

  /**
   * Wykonuje żądanie wygenerowania tokena reCAPTCHA v3 dla wyznaczonej akcji formularza.
   *
   * @param action - Nazwa akcji (np. 'login', 'register', 'password_reset').
   * @returns Obietnica zwracająca token reCAPTCHA lub undefined w przypadku braku konfiguracji.
   */
  const executeRecaptcha = useCallback(async (action: string): Promise<string | undefined> => {
    if (!SITE_KEY || typeof window === 'undefined' || scriptFailedRef.current) {
      return undefined
    }

    if (!window.grecaptcha) {
      const start = Date.now()
      while (
        !window.grecaptcha &&
        !scriptFailedRef.current &&
        Date.now() - start < SCRIPT_LOAD_TIMEOUT_MS
      ) {
        await new Promise((resolve) => setTimeout(resolve, 100))
      }
      if (!window.grecaptcha || scriptFailedRef.current) {
        return undefined
      }
    }

    return new Promise((resolve) => {
      let settled = false
      const finish = (token: string | undefined) => {
        if (settled) return
        settled = true
        clearTimeout(timeoutId)
        resolve(token)
      }

      const timeoutId = setTimeout(() => {
        finish(undefined)
      }, RECAPTCHA_READY_TIMEOUT_MS)

      try {
        window.grecaptcha?.ready(async () => {
          try {
            const token = await window.grecaptcha?.execute(SITE_KEY, { action })
            finish(token)
          } catch {
            finish(undefined)
          }
        })
      } catch {
        finish(undefined)
      }
    })
  }, [])

  return { executeRecaptcha, isRecaptchaConfigured: Boolean(SITE_KEY) }
}
