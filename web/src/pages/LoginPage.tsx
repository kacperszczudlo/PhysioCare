import { useEffect, useState, type FormEvent } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'

import { ApiError } from '@/api/client'
import { useAuth } from '@/auth/AuthContext'
import { setGoogleRegistrationDraft } from '@/auth/googleRegistrationDraft'
import { parseGoogleIdTokenClaims } from '@/auth/parseGoogleIdToken'
import { GoogleSignInButton, isWebGoogleSignInConfigured } from '@/components/GoogleSignInButton'
import { Button } from '@/components/ui/Button'
import { Field } from '@/components/ui/Field'
import { useToast } from '@/components/ui/ToastContext'
import './auth-forms.css'

export function LoginPage() {
  const { login, loginMFA, loginWithGoogle } = useAuth()
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

  const { toast } = useToast()
  const [email, setEmail] = useState(
    typeof locationState?.email === 'string' ? locationState.email : '',
  )
  const [password, setPassword] = useState('')
  const [mfaStep, setMfaStep] = useState<{ mfa_token: string; email: string } | null>(null)
  const [mfaCode, setMfaCode] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (notice) {
      toast.info(notice)
    }
  }, [notice, toast])

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError(null)
    const trimmedEmail = email.trim()
    if (!trimmedEmail) {
      setError('Podaj adres e-mail.')
      return
    }
    if (!password) {
      setError('Podaj hasło.')
      return
    }
    setLoading(true)
    try {
      const result = await login(trimmedEmail, password)
      if (result.kind === 'mfa_required') {
        setMfaStep({ mfa_token: result.mfa_token, email: result.email })
        return
      }
      navigate(from, { replace: true })
    } catch (err) {
      if (err instanceof ApiError && err.code === 'AUTH_027') {
        const details = err.details as { email?: string }
        const verifyEmail = (typeof details.email === 'string' && details.email) || trimmedEmail
        navigate(`/verify-email?email=${encodeURIComponent(verifyEmail)}`, { replace: true })
        return
      }
      setError(err instanceof ApiError ? err.message : 'Nie udało się zalogować.')
    } finally {
      setLoading(false)
    }
  }

  async function onMFASubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!mfaStep) return
    setError(null)
    setLoading(true)
    try {
      await loginMFA(mfaStep.mfa_token, mfaCode.trim())
      navigate(from, { replace: true })
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Nieprawidłowy kod 2FA.')
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
    } catch (err: unknown) {
      const errObj = err as Record<string, unknown> | null | undefined
      const detailsObj = (errObj?.details ||
        (errObj?.body as { error?: { details?: Record<string, unknown> } } | undefined)?.error
          ?.details) as Record<string, unknown> | undefined
      const isNotFound =
        errObj != null &&
        (errObj.code === 'AUTH_025' ||
          errObj.status === 404 ||
          Boolean(detailsObj?.needs_registration) ||
          (typeof errObj.message === 'string' &&
            /brak konta|nie znaleziono|dokończ rejestrację/i.test(errObj.message)))

      if (isNotFound) {
        const details = (detailsObj || {}) as {
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

  if (mfaStep) {
    return (
      <div className="auth-form">
        <header className="auth-form__header">
          <h1>Weryfikacja dwuskładnikowa (2FA)</h1>
          <p>Konto {mfaStep.email} wymaga potwierdzenia kodem z aplikacji Google Authenticator.</p>
        </header>

        <form className="auth-form__body" onSubmit={(e) => void onMFASubmit(e)} noValidate>
          <Field
            label="Kod z aplikacji weryfikującej lub kod zapasowy"
            name="mfaCode"
            type="text"
            placeholder="np. 123456 lub A8K2-M9X3"
            autoComplete="one-time-code"
            autoFocus
            required
            value={mfaCode}
            onChange={(e) => setMfaCode(e.target.value)}
          />

          {error ? (
            <p className="auth-form__error" role="alert">
              {error}
            </p>
          ) : null}

          <Button type="submit" loading={loading} className="auth-form__submit">
            Zaloguj się kodem 2FA
          </Button>

          <Button
            type="button"
            variant="secondary"
            onClick={() => {
              setMfaStep(null)
              setMfaCode('')
              setError(null)
            }}
          >
            Wróć do logowania
          </Button>
        </form>
      </div>
    )
  }

  return (
    <div className="auth-form">
      <header className="auth-form__header">
        <h1>Logowanie</h1>
        <p>Wejdź do panelu fizjoterapeuty.</p>
      </header>

      <form className="auth-form__body" onSubmit={(e) => void onSubmit(e)} noValidate>
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

        {error ? (
          <p className="auth-form__error" role="alert">
            {error}
          </p>
        ) : null}

        <Button
          type="submit"
          loading={loading}
          disabled={!email.trim() || !password}
          className="auth-form__submit"
        >
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
