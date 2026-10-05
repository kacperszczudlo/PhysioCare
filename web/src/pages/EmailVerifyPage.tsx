import { useState, type FormEvent } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'

import { authApi, type MFASetupResponse } from '@/api/auth'
import { ApiError } from '@/api/client'
import { useAuth } from '@/auth/AuthContext'
import { ErrorBanner } from '@/components/AsyncState'
import { Button } from '@/components/ui/Button'
import { Field } from '@/components/ui/Field'
import { useToast } from '@/components/ui/ToastContext'
import './auth-forms.css'

function qrSvgDataUri(svg: string): string {
  return `data:image/svg+xml;charset=utf-8,${encodeURIComponent(svg)}`
}

/**
 * Strona weryfikacji adresu e-mail kodem jednorazowym po rejestracji
 * oraz natychmiastowej konfiguracji 2FA dla fizjoterapeutów.
 */
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

  // Stan konfiguracji 2FA dla roli wymagającej MFA (fizjoterapeuta)
  const [mfaSetup, setMfaSetup] = useState<{
    token: string
    email: string
    data: MFASetupResponse
  } | null>(null)
  const [totpCode, setTotpCode] = useState('')
  const [backupCodes, setBackupCodes] = useState<string[] | null>(null)

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
      const result = await verifyEmail(email, cleaned)
      if (result.kind === 'authenticated') {
        navigate('/', { replace: true })
        return
      }
      if (result.kind === 'mfa_setup_required') {
        const setupData = await authApi.setupMFA(result.mfa_setup_token)
        setMfaSetup({
          token: result.mfa_setup_token,
          email: result.email,
          data: setupData,
        })
      }
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Nie udało się potwierdzić e-maila.')
    } finally {
      setLoading(false)
    }
  }

  async function onMFASubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!mfaSetup) return
    setError(null)
    const cleanedTotp = totpCode.trim().replace(/\s|-/g, '')
    if (!/^\d{6}$/.test(cleanedTotp)) {
      setError('Wpisz 6-cyfrowy kod z aplikacji uwierzytelniającej.')
      return
    }
    setLoading(true)
    try {
      const enableRes = await authApi.enableMFA(cleanedTotp, mfaSetup.token)
      setBackupCodes(enableRes.backup_codes)
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Nieprawidłowy kod 2FA. Spróbuj ponownie.')
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

  if (backupCodes) {
    return (
      <div className="auth-form">
        <header className="auth-form__header">
          <h1>Zapisz kody zapasowe</h1>
          <p>
            Dwuskładnikowa autentykacja została pomyślnie włączona. Zapisz poniższe jednorazowe kody
            zapasowe w bezpiecznym miejscu:
          </p>
        </header>

        <div className="auth-form__body">
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(2, 1fr)',
              gap: '0.5rem',
              background: 'var(--color-bg-subtle, #f3f4f6)',
              padding: '1rem',
              borderRadius: 'var(--radius-md, 8px)',
              fontFamily: 'monospace',
              fontSize: '1rem',
              textAlign: 'center',
            }}
          >
            {backupCodes.map((c) => (
              <span key={c} style={{ fontWeight: 600 }}>
                {c}
              </span>
            ))}
          </div>

          <p style={{ fontSize: 'var(--text-sm)', color: 'var(--color-muted)' }}>
            Każdy kod może być użyty tylko raz w sytuacji awaryjnej (np. utraty telefonu).
          </p>

          <Button
            type="button"
            className="auth-form__submit"
            onClick={() =>
              navigate('/login', {
                state: {
                  email,
                  notice:
                    'Konto i 2FA zostały pomyślnie skonfigurowane. Zaloguj się, aby przejść do panelu.',
                },
                replace: true,
              })
            }
          >
            Przejdź do logowania
          </Button>
        </div>
      </div>
    )
  }

  if (mfaSetup) {
    return (
      <div className="auth-form">
        <header className="auth-form__header">
          <h1>Krok 2: Skonfiguruj 2FA</h1>
          <p>
            Dla Twojego konta fizjoterapeuty wymagane jest uwierzytelnianie dwuskładnikowe (2FA).
            Zeskanuj poniższy kod w aplikacji Google Authenticator (lub innej zgodnej z TOTP).
          </p>
        </header>

        <form className="auth-form__body" onSubmit={(e) => void onMFASubmit(e)} noValidate>
          <img
            src={qrSvgDataUri(mfaSetup.data.qr_code_svg)}
            alt="Kod QR do konfiguracji aplikacji uwierzytelniającej"
            style={{ width: '220px', maxWidth: '100%', alignSelf: 'center' }}
          />
          <div style={{ textAlign: 'center' }}>
            <span style={{ fontSize: 'var(--text-xs)', color: 'var(--color-muted)' }}>
              Klucz konfiguracji ręcznej:
            </span>
            <br />
            <code style={{ fontSize: '0.9rem', wordBreak: 'break-all' }}>
              {mfaSetup.data.secret_key}
            </code>
          </div>

          <Field
            label="6-cyfrowy kod z aplikacji"
            name="totpCode"
            type="text"
            inputMode="numeric"
            autoComplete="one-time-code"
            autoFocus
            required
            placeholder="123456"
            value={totpCode}
            onChange={(e) => setTotpCode(e.target.value.replace(/\D/g, '').slice(0, 6))}
          />

          {error ? <ErrorBanner message={error} /> : null}

          <Button type="submit" loading={loading} className="auth-form__submit">
            Aktywuj 2FA i zakończ rejestrację
          </Button>
        </form>
      </div>
    )
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
