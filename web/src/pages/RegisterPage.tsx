import { useState, type FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'

import { ApiError, getFieldError } from '@/api/client'
import { useAuth } from '@/auth/AuthContext'
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

export function RegisterPage() {
  const { register } = useAuth()
  const navigate = useNavigate()

  const [firstName, setFirstName] = useState('')
  const [lastName, setLastName] = useState('')
  const [email, setEmail] = useState('')
  const [pwzf, setPwzf] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [declaration, setDeclaration] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [fieldErrors, setFieldErrors] = useState<{
    email?: string
    pwzf?: string
    password?: string
    confirmPassword?: string
  }>({})
  const [passwordTouched, setPasswordTouched] = useState(false)
  const [submitted, setSubmitted] = useState(false)
  const [loading, setLoading] = useState(false)

  const passwordHints = { email, firstName, lastName }
  const passwordRequirements = getPasswordRequirements(password, passwordHints)
  const showRequirementErrors = submitted || passwordTouched

  function getPwzfError(value: string): string | null {
    const normalized = value.trim()
    if (!normalized) {
      return 'Podaj numer PWZFz.'
    }
    if (normalized.length > 20) {
      return 'Numer PWZFz może mieć co najwyżej 20 znaków.'
    }
    return null
  }

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError(null)
    setSubmitted(true)

    const nextFieldErrors: {
      email?: string
      pwzf?: string
      password?: string
      confirmPassword?: string
    } = {}
    const emailError = getEmailError(email)
    if (emailError) {
      nextFieldErrors.email = emailError
    }
    const pwzfError = getPwzfError(pwzf)
    if (pwzfError) {
      nextFieldErrors.pwzf = pwzfError
    }
    const passwordError = getPasswordError(password, passwordHints)
    if (passwordError) {
      nextFieldErrors.password = passwordError
    }
    if (!passwordsMatch(password, confirmPassword)) {
      nextFieldErrors.confirmPassword = PASSWORD_MESSAGES.mismatch
    }

    if (!declaration) {
      setFieldErrors(nextFieldErrors)
      setError('Wymagane jest oświadczenie o posiadaniu numeru PWZFz.')
      return
    }

    if (
      nextFieldErrors.email ||
      nextFieldErrors.pwzf ||
      nextFieldErrors.password ||
      nextFieldErrors.confirmPassword
    ) {
      setFieldErrors(nextFieldErrors)
      return
    }

    setFieldErrors({})
    setLoading(true)
    try {
      await register({
        email: email.trim(),
        password,
        first_name: firstName.trim(),
        last_name: lastName.trim(),
        pwzf_number: pwzf.trim(),
        pwzf_declaration: true,
      })
      navigate('/', { replace: true })
    } catch (err) {
      const apiEmailError = getFieldError(err, 'email')
      const apiPwzfError = getFieldError(err, 'pwzf_number')
      const apiPasswordError = getFieldError(err, 'password')
      if (apiEmailError || apiPwzfError || apiPasswordError) {
        setFieldErrors({
          email: apiEmailError ?? undefined,
          pwzf: apiPwzfError ?? undefined,
          password: apiPasswordError ?? undefined,
        })
      }
      const message =
        err instanceof ApiError
          ? err.message
          : 'Nie udało się utworzyć konta. Sprawdź dane i spróbuj ponownie.'
      const duplicate =
        (apiEmailError && message === apiEmailError) ||
        (apiPwzfError && message === apiPwzfError) ||
        (apiPasswordError && message === apiPasswordError)
      setError(duplicate ? null : message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="auth-form">
      <header className="auth-form__header">
        <h1>Rejestracja terapeuty</h1>
        <p>Konto z numerem PWZFz — dostęp do panelu gabinetu.</p>
      </header>

      <form className="auth-form__body" onSubmit={onSubmit} noValidate>
        <div className="auth-form__row">
          <Field
            label="Imię"
            name="first_name"
            autoComplete="given-name"
            required
            value={firstName}
            onChange={(e) => setFirstName(e.target.value)}
          />
          <Field
            label="Nazwisko"
            name="last_name"
            autoComplete="family-name"
            required
            value={lastName}
            onChange={(e) => setLastName(e.target.value)}
          />
        </div>
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
        <Field
          label="Numer PWZFz"
          name="pwzf_number"
          required
          maxLength={20}
          value={pwzf}
          onChange={(e) => {
            setPwzf(e.target.value)
            if (fieldErrors.pwzf) {
              setFieldErrors((prev) => ({ ...prev, pwzf: undefined }))
            }
          }}
          error={fieldErrors.pwzf}
          hint="Numer prawa wykonywania zawodu fizjoterapeuty (max. 20 znaków)"
        />

        <div className="auth-form__password">
          <Field
            label="Hasło"
            name="password"
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
            aria-describedby="password-requirements"
          />
          <div id="password-requirements" className="auth-form__password-reqs">
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

        <label className="auth-form__check">
          <input
            type="checkbox"
            checked={declaration}
            onChange={(e) => setDeclaration(e.target.checked)}
          />
          <span>Oświadczam, że posiadam ważne prawo wykonywania zawodu (PWZFz).</span>
        </label>

        {error ? (
          <p className="auth-form__error" role="alert">
            {error}
          </p>
        ) : null}

        <Button type="submit" loading={loading} className="auth-form__submit">
          Utwórz konto
        </Button>
      </form>

      <p className="auth-form__footer">
        Masz już konto? <Link to="/login">Zaloguj się</Link>
      </p>
    </div>
  )
}
