import { useState } from 'react'

import { requestGoogleIdTokenPopup } from '@/auth/googleIdTokenPopup'
import { GoogleMark } from '@/components/GoogleMark'

import './GoogleSignInButton.css'

const googleClientId = import.meta.env.VITE_GOOGLE_CLIENT_ID?.trim() ?? ''

// eslint-disable-next-line react-refresh/only-export-components
export function isWebGoogleSignInConfigured(): boolean {
  return Boolean(googleClientId)
}

type GoogleSignInButtonProps = {
  disabled?: boolean
  title?: string
  hint?: string
  onCredential: (credential: string) => void | Promise<void>
  onError: (message: string) => void
}

export function GoogleSignInButton({
  disabled = false,
  title = 'Kontynuuj z Google',
  hint,
  onCredential,
  onError,
}: GoogleSignInButtonProps) {
  const [busy, setBusy] = useState(false)

  if (!googleClientId) {
    return null
  }

  async function onPress() {
    if (busy || disabled) {
      return
    }
    setBusy(true)
    try {
      const credential = await requestGoogleIdTokenPopup(googleClientId)
      await onCredential(credential)
    } catch (error) {
      onError(
        error instanceof Error && error.message
          ? error.message
          : 'Logowanie Google nie powiodło się.',
      )
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="google-auth">
      <p className="google-auth__divider" role="separator">
        lub
      </p>
      <button
        type="button"
        className="google-auth__btn"
        disabled={disabled || busy}
        aria-busy={busy}
        onClick={() => {
          void onPress()
        }}
      >
        {busy ? (
          <span className="google-auth__spinner" aria-hidden="true" />
        ) : (
          <>
            <GoogleMark className="google-auth__mark" size={18} />
            <span className="google-auth__label">{title}</span>
          </>
        )}
      </button>
      {hint ? <p className="google-auth__hint">{hint}</p> : null}
    </div>
  )
}
