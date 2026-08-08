import { useState, type FormEvent } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'

import { ApiError } from '@/api/client'
import { useAuth } from '@/auth/AuthContext'
import { Button } from '@/components/ui/Button'
import { Field } from '@/components/ui/Field'
import './auth-forms.css'

export function LoginPage() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const from = (location.state as { from?: { pathname?: string } } | null)?.from?.pathname ?? '/'

  const [email, setEmail] = useState('')
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
      setError(err instanceof ApiError ? err.message : 'Nie udało się zalogować.')
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

        {error ? (
          <p className="auth-form__error" role="alert">
            {error}
          </p>
        ) : null}

        <Button type="submit" loading={loading} className="auth-form__submit">
          Zaloguj się
        </Button>
      </form>

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
