import { useState, type FormEvent } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'

import { ApiError } from '@/api/client'
import { useAuth } from '@/auth/AuthContext'
import { setGoogleRegistrationDraft } from '@/auth/googleRegistrationDraft'
import { parseGoogleIdTokenClaims } from '@/auth/parseGoogleIdToken'
import { SuccessBanner } from '@/components/AsyncState'
import { GoogleSignInButton, isWebGoogleSignInConfigured } from '@/components/GoogleSignInButton'
import { Button } from '@/components/ui/Button'
import { Field } from '@/components/ui/Field'
import './auth-forms.css'

export function LoginPage() {
  const { login, loginWithGoogle } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const locationState = location.state as {
    from?: { pathname?: string }
    notice?: string
    email?: string
  } | null
  const from = locationState?.from?.pathname ?? '/'
  const notice =
    typeof locationState?.notice === 'string' && locationState.notice.trim()
      ? locationState.notice.trim()
      : null

  const [email, setEmail] = useState(
    typeof locationState?.email === 'string' ? locationState.email : '',
  )
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError(null)
    setLoading(true)
    try {
      await login(email.trim(), password)
      navigate(from, { replace: true })
    } catch (err) {
      if (err instanceof ApiError && err.code === 'AUTH_027') {
        const details = err.details as { email?: string }
        const verifyEmail = (typeof details.email === 'string' && details.email) || email.trim()
        navigate(`/verify-email?email=${encodeURIComponent(verifyEmail)}`, { replace: true })
        return
      }
      setError(err instanceof ApiError ? err.message : 'Nie udało się zalogować.')
    } finally {
      setLoading(false)
    }
  }

  async function onGoogleCredential(credential: string) {
    setError(null)
    setLoading(true)
    try {
      await loginWithGoogle(credential)
      navigate(from, { replace: true })
    } catch (err) {
      if (err instanceof ApiError && err.code === 'AUTH_025') {
        const details = err.details as {
          email?: string
          first_name?: string
          last_name?: string
        }
        const claims = parseGoogleIdTokenClaims(credential)
        setGoogleRegistrationDraft({
          credential,
          email: (typeof details.email === 'string' && details.email) || claims.email || undefined,
          first_name:
            (typeof details.first_name === 'string' && details.first_name) ||
            claims.first_name ||
            undefined,
          last_name:
            (typeof details.last_name === 'string' && details.last_name) ||
            claims.last_name ||
            undefined,
        })
        navigate('/register', { replace: true })
        return
      }
      setError(err instanceof ApiError ? err.message : 'Nie udało się zalogować przez Google.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="auth-form">
      <header className="auth-form__header">
        <h1>Logowanie</h1>
        <p>Wejdź do panelu fizjoterapeuty.</p>
      </header>

      <form className="auth-form__body" onSubmit={onSubmit} noValidate>
        <Field
          label="E-mail"
          name="email"
          type="email"
          autoComplete="email"
          required
          value={email}
          onChange={(e) => setEmail(e.target.value)}
        />
        <Field
          label="Hasło"
          name="password"
          type="password"
          autoComplete="current-password"
          required
          value={password}
          onChange={(e) => setPassword(e.target.value)}
        />

        {notice ? <SuccessBanner message={notice} /> : null}
        {error ? (
          <p className="auth-form__error" role="alert">
            {error}
          </p>
        ) : null}

        <Button type="submit" loading={loading} className="auth-form__submit">
          Zaloguj się
        </Button>
      </form>

      {isWebGoogleSignInConfigured() ? (
        <GoogleSignInButton
          disabled={loading}
          title="Kontynuuj z Google"
          hint="Nowe konto? Google przeniesie Cię do rejestracji z uzupełnionym e-mailem i imieniem - zostaje PWZFz."
          onCredential={onGoogleCredential}
          onError={setError}
        />
      ) : null}

      <p className="auth-form__footer">
        <Link to="/register">Załóż konto (PWZFz)</Link>
        <span aria-hidden="true">·</span>
        <Link to="/password-reset">Nie pamiętam hasła</Link>
        <span aria-hidden="true">·</span>
        <Link to="/privacy">Prywatność</Link>
      </p>
    </div>
  )
}
