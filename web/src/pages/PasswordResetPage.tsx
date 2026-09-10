import { useState, type FormEvent } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'

import { ApiError, getFieldError } from '@/api/client'
import { useAuth } from '@/auth/AuthContext'
import { ErrorBanner, SuccessBanner } from '@/components/AsyncState'
import { Button } from '@/components/ui/Button'
import { Field } from '@/components/ui/Field'
import { PasswordRequirements } from '@/components/ui/PasswordRequirements'
import { getEmailError } from '@/lib/emailPolicy'
import {
  getPasswordError,
  getPasswordRequirements,
  PASSWORD_MESSAGES,
  passwordsMatch,
} from '@/lib/passwordPolicy'
import './auth-forms.css'

type Step = 'request' | 'code' | 'password'

export function PasswordResetPage() {
  const {
    requestPasswordReset,
    verifyPasswordResetCode,
    confirmPasswordReset,
    logout,
    isAuthenticated,
  } = useAuth()
  const navigate = useNavigate()
  const [params] = useSearchParams()
  const emailFromQuery = (params.get('email') ?? '').trim()

  const [step, setStep] = useState<Step>('request')
  const [email, setEmail] = useState(emailFromQuery)
  const [code, setCode] = useState('')
  const [resetToken, setResetToken] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [message, setMessage] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [fieldErrors, setFieldErrors] = useState<{
    email?: string
    code?: string
    password?: string
    confirmPassword?: string
  }>({})
  const [passwordTouched, setPasswordTouched] = useState(false)
  const [submitted, setSubmitted] = useState(false)
  const [loading, setLoading] = useState(false)

  const passwordRequirements = getPasswordRequirements(password)
  const showRequirementErrors = submitted || passwordTouched

  function goToRequest() {
    setStep('request')
    setCode('')
    setResetToken('')
    setPassword('')
    setConfirmPassword('')
    setMessage(null)
    setError(null)
    setFieldErrors({})
    setPasswordTouched(false)
    setSubmitted(false)
  }

  function goToCodeStep(notice?: string | null) {
    setStep('code')
    setCode('')
    setResetToken('')
    setPassword('')
    setConfirmPassword('')
    setPasswordTouched(false)
    setSubmitted(false)
    setFieldErrors({})
    setError(null)
    setMessage(notice ?? null)
  }

  async function onRequest(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError(null)
    setMessage(null)
    const emailError = getEmailError(email)
    if (emailError) {
      setFieldErrors({ email: emailError })
      return
    }
    setFieldErrors({})
    setLoading(true)
    try {
      const detail = await requestPasswordReset(email.trim())
      goToCodeStep(detail)
    } catch (err) {
      const apiEmailError = getFieldError(err, 'email')
      if (apiEmailError) {
        setFieldErrors({ email: apiEmailError })
        setError(null)
      } else {
        setError(err instanceof ApiError ? err.message : 'Nie udało się wysłać kodu.')
      }
    } finally {
      setLoading(false)
    }
  }

  async function onResendCode() {
    setError(null)
    setMessage(null)
    setLoading(true)
    try {
      const detail = await requestPasswordReset(email.trim())
      setCode('')
      setResetToken('')
      setStep('code')
      setMessage(detail)
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Nie udało się wysłać kodu ponownie.')
    } finally {
      setLoading(false)
    }
  }

  async function onVerifyCode(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError(null)
    setMessage(null)
    const cleaned = code.trim()
    if (!/^\d{6}$/.test(cleaned)) {
      setFieldErrors({ code: 'Wpisz 6-cyfrowy kod z e-maila.' })
      return
    }
    setFieldErrors({})
    setLoading(true)
    try {
      const token = await verifyPasswordResetCode(email.trim(), cleaned)
      setResetToken(token)
      setPassword('')
      setConfirmPassword('')
      setMessage(null)
      setError(null)
      setStep('password')
    } catch (err) {
      const apiCodeError = getFieldError(err, 'code')
      if (apiCodeError) {
        setFieldErrors({ code: apiCodeError })
        setError(null)
      } else {
        setError(err instanceof ApiError ? err.message : 'Nie udało się zweryfikować kodu.')
      }
    } finally {
      setLoading(false)
    }
  }

  async function onSetPassword(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError(null)
    setMessage(null)
    setSubmitted(true)

    const nextFieldErrors: { password?: string; confirmPassword?: string } = {}
    const passwordError = getPasswordError(password)
    if (passwordError) {
      nextFieldErrors.password = passwordError
    }
    if (!passwordsMatch(password, confirmPassword)) {
      nextFieldErrors.confirmPassword = PASSWORD_MESSAGES.mismatch
    }
    if (nextFieldErrors.password || nextFieldErrors.confirmPassword) {
      setFieldErrors(nextFieldErrors)
      return
    }
    if (!resetToken) {
      goToCodeStep('Sesja resetu wygasła. Wyślij kod ponownie.')
      return
    }

    setFieldErrors({})
    setLoading(true)
    try {
      await confirmPasswordReset({
        reset_token: resetToken,
        new_password: password,
        new_password_confirm: confirmPassword,
      })
      if (isAuthenticated) {
        await logout().catch(() => undefined)
      }
      navigate('/login', {
        replace: true,
        state: {
          notice: 'Hasło zostało zmienione. Zaloguj się nowym hasłem.',
          email: email.trim(),
        },
      })
    } catch (err) {
      const apiPasswordError = getFieldError(err, 'new_password') ?? getFieldError(err, 'password')
      if (apiPasswordError) {
        setFieldErrors({ password: apiPasswordError })
        setError(null)
        return
      }
      const msg = err instanceof ApiError ? err.message : 'Nie udało się zmienić hasła.'
      if (err instanceof ApiError && err.code === 'AUTH_028') {
        goToCodeStep(`${msg} Wyślij kod ponownie.`)
        return
      }
      setError(msg)
    } finally {
      setLoading(false)
    }
  }

  const title =
    step === 'code' ? 'Kod z e-maila' : step === 'password' ? 'Nowe hasło' : 'Reset hasła'
  const subtitle =
    step === 'code'
      ? `Wysłaliśmy 6-cyfrowy kod${email.trim() ? ` na ${email.trim()}` : ''}. Wpisz go poniżej.`
      : step === 'password'
        ? 'Ustaw nowe hasło i powtórz je, żeby potwierdzić.'
        : 'Podaj e-mail powiązany z kontem. Wyślemy 6-cyfrowy kod resetu hasła.'

  return (
    <div className="auth-form">
      <header className="auth-form__header">
        <h1>{title}</h1>
        <p>{subtitle}</p>
      </header>

      {step === 'code' ? (
        <form className="auth-form__body" onSubmit={onVerifyCode} noValidate>
          <Field
            label="Kod z e-maila"
            name="code"
            inputMode="numeric"
            autoComplete="one-time-code"
            required
            value={code}
            onChange={(e) => {
              setCode(e.target.value.replace(/\D/g, '').slice(0, 6))
              if (fieldErrors.code) {
                setFieldErrors((prev) => ({ ...prev, code: undefined }))
              }
            }}
            error={fieldErrors.code}
          />
          {error ? <ErrorBanner message={error} /> : null}
          {message ? <SuccessBanner message={message} /> : null}
          <Button type="submit" loading={loading} className="auth-form__submit">
            Potwierdź kod
          </Button>
          <Button
            type="button"
            variant="secondary"
            disabled={loading}
            onClick={() => void onResendCode()}
          >
            Wyślij kod ponownie
          </Button>
          <Button type="button" variant="secondary" disabled={loading} onClick={goToRequest}>
            Zmień e-mail
          </Button>
        </form>
      ) : step === 'password' ? (
        <form className="auth-form__body" onSubmit={onSetPassword} noValidate>
          <div className="auth-form__password">
            <Field
              label="Nowe hasło"
              name="new_password"
              type="password"
              autoComplete="new-password"
              required
              value={password}
              onChange={(e) => {
                setPassword(e.target.value)
                if (fieldErrors.password) {
                  setFieldErrors((prev) => ({ ...prev, password: undefined }))
                }
              }}
              onBlur={() => setPasswordTouched(true)}
              error={fieldErrors.password}
              aria-describedby="reset-password-requirements"
            />
            <div id="reset-password-requirements" className="auth-form__password-reqs">
              <PasswordRequirements
                requirements={passwordRequirements}
                showErrors={showRequirementErrors}
              />
            </div>
            <Field
              label="Powtórz hasło"
              name="confirm_password"
              type="password"
              autoComplete="new-password"
              required
              value={confirmPassword}
              onChange={(e) => {
                setConfirmPassword(e.target.value)
                if (fieldErrors.confirmPassword) {
                  setFieldErrors((prev) => ({ ...prev, confirmPassword: undefined }))
                }
              }}
              error={fieldErrors.confirmPassword}
            />
          </div>
          {error ? <ErrorBanner message={error} /> : null}
          <Button type="submit" loading={loading} className="auth-form__submit">
            Zapisz hasło
          </Button>
          <Button
            type="button"
            variant="secondary"
            disabled={loading}
            onClick={() => void onResendCode()}
          >
            Wyślij kod ponownie
          </Button>
        </form>
      ) : (
        <form className="auth-form__body" onSubmit={onRequest} noValidate>
          <Field
            label="E-mail"
            name="email"
            type="email"
            autoComplete="email"
            required
            value={email}
            onChange={(e) => {
              setEmail(e.target.value)
              if (fieldErrors.email) {
                setFieldErrors((prev) => ({ ...prev, email: undefined }))
              }
            }}
            error={fieldErrors.email}
          />
          {error ? <ErrorBanner message={error} /> : null}
          {message ? <SuccessBanner message={message} /> : null}
          <Button type="submit" loading={loading} className="auth-form__submit">
            Wyślij kod
          </Button>
        </form>
      )}

      <p className="auth-form__footer">
        <Link to="/login">Wróć do logowania</Link>
      </p>
    </div>
  )
}
