import { useState, type FormEvent } from 'react'
import { Link, useSearchParams } from 'react-router-dom'

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

export function PasswordResetPage() {
  const { requestPasswordReset, confirmPasswordReset } = useAuth()
  const [params] = useSearchParams()
  const tokenFromUrl = params.get('token') ?? ''

  const [email, setEmail] = useState('')
  const [token, setToken] = useState(tokenFromUrl)
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [message, setMessage] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [fieldErrors, setFieldErrors] = useState<{
    email?: string
    password?: string
    confirmPassword?: string
  }>({})
  const [passwordTouched, setPasswordTouched] = useState(false)
  const [submitted, setSubmitted] = useState(false)
  const [loading, setLoading] = useState(false)

  const isConfirmMode = Boolean(tokenFromUrl || token)
  const passwordRequirements = getPasswordRequirements(password)
  const showRequirementErrors = submitted || passwordTouched

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
      setMessage(detail)
    } catch (err) {
      const apiEmailError = getFieldError(err, 'email')
      if (apiEmailError) {
        setFieldErrors({ email: apiEmailError })
        setError(null)
      } else {
        setError(err instanceof ApiError ? err.message : 'Nie udało się wysłać prośby.')
      }
    } finally {
      setLoading(false)
    }
  }

  async function onConfirm(event: FormEvent<HTMLFormElement>) {
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

    setFieldErrors({})
    setLoading(true)
    try {
      const detail = await confirmPasswordReset({
        token: token.trim(),
        new_password: password,
      })
      setMessage(detail)
    } catch (err) {
      const apiPasswordError = getFieldError(err, 'new_password') ?? getFieldError(err, 'password')
      if (apiPasswordError) {
        setFieldErrors({ password: apiPasswordError })
      }
      const msg = err instanceof ApiError ? err.message : 'Nie udało się zmienić hasła.'
      setError(apiPasswordError && msg === apiPasswordError ? null : msg)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="auth-form">
      <header className="auth-form__header">
        <h1>{isConfirmMode ? 'Nowe hasło' : 'Reset hasła'}</h1>
        <p>
          {isConfirmMode
            ? 'Ustaw nowe hasło na podstawie tokenu z e-maila.'
            : 'Wyślemy link resetujący, jeśli konto istnieje.'}
        </p>
      </header>

      {isConfirmMode ? (
        <form className="auth-form__body" onSubmit={onConfirm} noValidate>
          {!tokenFromUrl ? (
            <Field
              label="Token"
              name="token"
              required
              value={token}
              onChange={(e) => setToken(e.target.value)}
            />
          ) : null}
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
          {message ? (
            <SuccessBanner
              message={
                <p>
                  {message} <Link to="/login">Przejdź do logowania</Link>
                </p>
              }
            />
          ) : null}
          <Button type="submit" loading={loading} className="auth-form__submit">
            Zapisz hasło
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
            Wyślij link
          </Button>
        </form>
      )}

      <p className="auth-form__footer">
        <Link to="/login">Wróć do logowania</Link>
      </p>
    </div>
  )
}
