import { useState, type FormEvent } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'

import { ApiError } from '@/api/client'
import { useAuth } from '@/auth/AuthContext'
import { ErrorBanner } from '@/components/AsyncState'
import { Button } from '@/components/ui/Button'
import { Field } from '@/components/ui/Field'
import { useToast } from '@/components/ui/ToastContext'
import './auth-forms.css'

export function EmailVerifyPage() {
  const { verifyEmail, resendEmailCode } = useAuth()
  const { toast } = useToast()
  const navigate = useNavigate()
  const [params] = useSearchParams()
  const emailFromQuery = (params.get('email') ?? '').trim()

  const [email] = useState(emailFromQuery)
  const [code, setCode] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError(null)
    if (!email) {
      setError('Brak adresu e-mail. Wróć do rejestracji lub logowania.')
      return
    }
    const cleaned = code.trim()
    if (!/^\d{6}$/.test(cleaned)) {
      setError('Wpisz 6-cyfrowy kod z wiadomości e-mail.')
      return
    }
    setLoading(true)
    try {
      await verifyEmail(email, cleaned)
      navigate('/', { replace: true })
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Nie udało się potwierdzić e-maila.')
    } finally {
      setLoading(false)
    }
  }

  async function onResend() {
    if (!email) {
      setError('Brak adresu e-mail.')
      return
    }
    setError(null)
    setLoading(true)
    try {
      const detail = await resendEmailCode(email)
      toast.success(detail, { title: 'Kod wysłany' })
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Nie udało się wysłać kodu.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="auth-form">
      <header className="auth-form__header">
        <h1>Potwierdź e-mail</h1>
        <p>
          Wysłaliśmy 6-cyfrowy kod
          {email ? (
            <>
              {' '}
              na <strong>{email}</strong>
            </>
          ) : null}
          . Wpisz go poniżej, aby aktywować konto.
        </p>
      </header>

      <form className="auth-form__body" onSubmit={onSubmit} noValidate>
        <Field
          label="Kod z e-maila"
          name="code"
          inputMode="numeric"
          autoComplete="one-time-code"
          required
          value={code}
          onChange={(e) => setCode(e.target.value.replace(/\D/g, '').slice(0, 6))}
        />
        {error ? <ErrorBanner message={error} /> : null}
        <Button type="submit" loading={loading} className="auth-form__submit">
          Potwierdź
        </Button>
        <Button
          type="button"
          variant="secondary"
          disabled={loading}
          onClick={() => void onResend()}
        >
          Wyślij kod ponownie
        </Button>
      </form>

      <p className="auth-form__footer">
        <Link to="/login">Wróć do logowania</Link>
      </p>
    </div>
  )
}
