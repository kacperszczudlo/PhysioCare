import { useCallback, useEffect } from 'react'

declare global {
  interface Window {
    grecaptcha?: {
      ready: (callback: () => void) => void
      execute: (siteKey: string, options: { action: string }) => Promise<string>
    }
  }
}

const SITE_KEY = (import.meta.env.VITE_RECAPTCHA_SITE_KEY as string | undefined) || ''

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
  useEffect(() => {
    if (!SITE_KEY) return

    const scriptId = 'google-recaptcha-script'
    if (document.getElementById(scriptId)) return

    const script = document.createElement('script')
    script.id = scriptId
    script.src = `https://www.google.com/recaptcha/api.js?render=${encodeURIComponent(SITE_KEY)}`
    script.async = true
    document.head.appendChild(script)
  }, [])

  /**
   * Wykonuje żądanie wygenerowania tokena reCAPTCHA v3 dla wyznaczonej akcji formularza.
   *
   * @param action - Nazwa akcji (np. 'login', 'register', 'password_reset').
   * @returns Obietnica zwracająca token reCAPTCHA lub undefined w przypadku braku konfiguracji.
   */
  const executeRecaptcha = useCallback(async (action: string): Promise<string | undefined> => {
    if (!SITE_KEY || typeof window === 'undefined') {
      return undefined
    }

    if (!window.grecaptcha) {
      const start = Date.now()
      while (!window.grecaptcha && Date.now() - start < 2500) {
        await new Promise((resolve) => setTimeout(resolve, 100))
      }
      if (!window.grecaptcha) {
        return undefined
      }
    }

    return new Promise((resolve) => {
      window.grecaptcha?.ready(async () => {
        try {
          const token = await window.grecaptcha?.execute(SITE_KEY, { action })
          resolve(token)
        } catch {
          resolve(undefined)
        }
      })
    })
  }, [])

  return { executeRecaptcha, isRecaptchaConfigured: Boolean(SITE_KEY) }
}
