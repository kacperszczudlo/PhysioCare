import { useState, type FormEvent } from 'react'
import { Link, useSearchParams } from 'react-router-dom'

import { ApiError } from '@/api/client'
import { useAuth } from '@/auth/AuthContext'
import { Button } from '@/components/ui/Button'
import { Field } from '@/components/ui/Field'
import './auth-forms.css'

export function PasswordResetPage() {
  const { requestPasswordReset, confirmPasswordReset } = useAuth()
  const [params] = useSearchParams()
  const tokenFromUrl = params.get('token') ?? ''

  const [email, setEmail] = useState('')
  const [token, setToken] = useState(tokenFromUrl)
  const [password, setPassword] = useState('')
  const [message, setMessage] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  const isConfirmMode = Boolean(tokenFromUrl || token)

  async function onRequest(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError(null)
    setMessage(null)
    setLoading(true)
    try {
      const detail = await requestPasswordReset(email.trim())
      setMessage(detail)
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Nie udało się wysłać prośby.')
    } finally {
      setLoading(false)
    }
  }

  async function onConfirm(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError(null)
    setMessage(null)
    setLoading(true)
    try {
      const detail = await confirmPasswordReset({
        token: token.trim(),
        new_password: password,
      })
      setMessage(detail)
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Nie udało się zmienić hasła.')
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
          <Field
            label="Nowe hasło"
            name="new_password"
            type="password"
            autoComplete="new-password"
            required
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
          {error ? (
            <p className="auth-form__error" role="alert">
              {error}
            </p>
          ) : null}
          {message ? (
            <p className="auth-form__success" role="status">
              {message} <Link to="/login">Przejdź do logowania</Link>
            </p>
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
            onChange={(e) => setEmail(e.target.value)}
          />
          {error ? (
            <p className="auth-form__error" role="alert">
              {error}
            </p>
          ) : null}
          {message ? (
            <p className="auth-form__success" role="status">
              {message}
            </p>
          ) : null}
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
