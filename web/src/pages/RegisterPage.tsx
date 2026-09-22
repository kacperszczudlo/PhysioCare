import { useEffect, useState, type FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'

import { ApiError, getFieldError } from '@/api/client'
import type { QualificationLevel } from '@/api/types'
import { useAuth } from '@/auth/AuthContext'
import {
  peekGoogleRegistrationDraft,
  takeGoogleRegistrationDraft,
  type GoogleRegistrationDraft,
} from '@/auth/googleRegistrationDraft'
import { parseGoogleIdTokenClaims } from '@/auth/parseGoogleIdToken'
import { GoogleSignInButton, isWebGoogleSignInConfigured } from '@/components/GoogleSignInButton'
import { Button } from '@/components/ui/Button'
import { Field } from '@/components/ui/Field'
import { PasswordRequirements } from '@/components/ui/PasswordRequirements'
import { PhoneField } from '@/components/ui/PhoneField'
import { useToast } from '@/components/ui/ToastContext'
import { DEFAULT_COUNTRY_CODE } from '@/lib/countries'
import { getEmailError } from '@/lib/emailPolicy'
import { getFirstNameError, getLastNameError } from '@/lib/fieldPolicy'
import {
  getPasswordError,
  getPasswordRequirements,
  PASSWORD_MESSAGES,
  passwordsMatch,
} from '@/lib/passwordPolicy'
import { formatPhoneForApi, getPhoneError } from '@/lib/phonePolicy'
import { getPwzfError, normalizePwzf } from '@/lib/pwzfPolicy'
import { useRecaptcha } from '@/hooks/useRecaptcha'
import './auth-forms.css'

const QUALIFICATION_TILES: ReadonlyArray<{
  value: QualificationLevel
  title: string
  sub: string
}> = [
  {
    value: 'MAGISTER',
    title: 'Magister fizjoterapii',
    sub: 'Samodzielne planowanie i ordynacja wyrobów medycznych',
  },
  {
    value: 'LICENCJAT',
    title: 'Licencjat fizjoterapii',
    sub: 'Podstawowe planowanie i realizacja świadczeń',
  },
  {
    value: 'FIZJO_SPEC',
    title: 'Specjalista (FIZJO SPEC)',
    sub: 'Zaawansowany sprzęt i pełny zakres diagnostyki',
  },
  {
    value: 'TECHNIK',
    title: 'Technik fizjoterapii',
    sub: 'Realizacja zabiegów fizjoterapeutycznych',
  },
]

/**
 * Widok formularza rejestracji konta fizjoterapeuty z walidacją numeru PWZF, oświadczeniem prawnym i weryfikacją e-mail.
 */
export function RegisterPage() {
  const { register } = useAuth()
  const { executeRecaptcha } = useRecaptcha()
  const navigate = useNavigate()
  const { toast } = useToast()

  const [googleDraft, setGoogleDraft] = useState<GoogleRegistrationDraft | null>(() =>
    peekGoogleRegistrationDraft(),
  )
  const [firstName, setFirstName] = useState(() => peekGoogleRegistrationDraft()?.first_name ?? '')
  const [lastName, setLastName] = useState(() => peekGoogleRegistrationDraft()?.last_name ?? '')
  const [email, setEmail] = useState(() => peekGoogleRegistrationDraft()?.email ?? '')
  const [countryCode, setCountryCode] = useState(DEFAULT_COUNTRY_CODE)
  const [phoneNational, setPhoneNational] = useState('')
  const [pwzf, setPwzf] = useState('')
  const [qualificationLevel, setQualificationLevel] = useState<QualificationLevel>('MAGISTER')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [declaration, setDeclaration] = useState(false)
  const [infoMessage, setInfoMessage] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [fieldErrors, setFieldErrors] = useState<{
    firstName?: string
    lastName?: string
    email?: string
    phone?: string
    pwzf?: string
    password?: string
    confirmPassword?: string
  }>({})
  const [passwordTouched, setPasswordTouched] = useState(false)
  const [submitted, setSubmitted] = useState(false)
  const [loading, setLoading] = useState(false)

  const googleMode = Boolean(googleDraft?.credential)
  const passwordHints = { email, firstName, lastName }
  const passwordRequirements = getPasswordRequirements(password, passwordHints)
  const showRequirementErrors = submitted || passwordTouched

  useEffect(() => {
    const draft = takeGoogleRegistrationDraft()
    if (!draft) {
      return
    }
    setGoogleDraft(draft)
    if (draft.email) {
      setEmail(draft.email)
    }
    if (draft.first_name) {
      setFirstName(draft.first_name)
    }
    if (draft.last_name) {
      setLastName(draft.last_name)
    }
    setInfoMessage('Połączono z Google. Uzupełnij formularz, aby utworzyć konto.')
  }, [])

  function validateTherapistFields(requirePassword: boolean) {
    const nextFieldErrors: {
      firstName?: string
      lastName?: string
      email?: string
      phone?: string
      pwzf?: string
      password?: string
      confirmPassword?: string
    } = {}

    const firstNameError = getFirstNameError(firstName)
    if (firstNameError) {
      nextFieldErrors.firstName = firstNameError
    }
    const lastNameError = getLastNameError(lastName)
    if (lastNameError) {
      nextFieldErrors.lastName = lastNameError
    }

    if (requirePassword) {
      const emailError = getEmailError(email)
      if (emailError) {
        nextFieldErrors.email = emailError
      }
      const passwordError = getPasswordError(password, passwordHints)
      if (passwordError) {
        nextFieldErrors.password = passwordError
      }
      if (!passwordsMatch(password, confirmPassword)) {
        nextFieldErrors.confirmPassword = PASSWORD_MESSAGES.mismatch
      }
    }

    const phoneError = getPhoneError(phoneNational, countryCode)
    if (phoneError) {
      nextFieldErrors.phone = phoneError
    }
    const pwzfError = getPwzfError(pwzf)
    if (pwzfError) {
      nextFieldErrors.pwzf = pwzfError
    }

    return nextFieldErrors
  }

  function handleRegisterError(err: unknown) {
    const apiFirstNameError = getFieldError(err, 'first_name')
    const apiLastNameError = getFieldError(err, 'last_name')
    const apiEmailError = getFieldError(err, 'email')
    const apiPhoneError = getFieldError(err, 'phone')
    const apiPwzfError = getFieldError(err, 'pwzf_number')
    const apiPasswordError = getFieldError(err, 'password')
    const apiGoogleError = getFieldError(err, 'google_credential')
    if (
      apiFirstNameError ||
      apiLastNameError ||
      apiEmailError ||
      apiPhoneError ||
      apiPwzfError ||
      apiPasswordError
    ) {
      setFieldErrors({
        firstName: apiFirstNameError ?? undefined,
        lastName: apiLastNameError ?? undefined,
        email: apiEmailError ?? undefined,
        phone: apiPhoneError ?? undefined,
        pwzf: apiPwzfError ?? undefined,
        password: apiPasswordError ?? undefined,
      })
    }

    const accountExists =
      Boolean(apiEmailError && /już zarejestrowany/i.test(apiEmailError)) ||
      Boolean(apiGoogleError && /już istnieje/i.test(apiGoogleError))

    if (accountExists) {
      setGoogleDraft(null)
      setError(
        `${apiEmailError || apiGoogleError || 'Ten adres e-mail jest już zarejestrowany.'} ` +
          'Przejdź do logowania (Google lub hasło).',
      )
      return
    }

    const message =
      apiGoogleError ||
      (err instanceof ApiError
        ? err.message
        : 'Nie udało się utworzyć konta. Sprawdź dane i spróbuj ponownie.')
    const duplicate =
      (apiEmailError && message === apiEmailError) ||
      (apiPwzfError && message === apiPwzfError) ||
      (apiPasswordError && message === apiPasswordError)
    setError(duplicate ? null : message)
  }

  async function finishGoogleRegistration(credential: string) {
    const nextFieldErrors = validateTherapistFields(false)
    if (!declaration) {
      setFieldErrors(nextFieldErrors)
      setError('Zaznacz oświadczenie PWZFz, żeby dokończyć rejestrację Google.')
      return
    }
    if (
      nextFieldErrors.firstName ||
      nextFieldErrors.lastName ||
      nextFieldErrors.phone ||
      nextFieldErrors.pwzf
    ) {
      setFieldErrors(nextFieldErrors)
      setError(
        'Uzupełnij wymagane pola (imię, nazwisko, PWZFz), żeby dokończyć rejestrację Google.',
      )
      return
    }

    setFieldErrors({})
    setLoading(true)
    try {
      const recaptcha_token = await executeRecaptcha('register_google')
      const result = await register({
        google_credential: credential,
        recaptcha_token,
        first_name: firstName.trim(),
        last_name: lastName.trim(),
        pwzf_number: normalizePwzf(pwzf),
        pwzf_declaration: true,
        phone: formatPhoneForApi(phoneNational, countryCode) || undefined,
        qualification_level: qualificationLevel,
      })
      setGoogleDraft(null)
      if (result.kind === 'needs_email_verification') {
        navigate(`/verify-email?email=${encodeURIComponent(result.email)}`, { replace: true })
        return
      }
      navigate('/', { replace: true })
    } catch (err) {
      handleRegisterError(err)
    } finally {
      setLoading(false)
    }
  }

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError(null)
    setSubmitted(true)

    if (googleMode && googleDraft?.credential) {
      await finishGoogleRegistration(googleDraft.credential)
      return
    }

    const nextFieldErrors = validateTherapistFields(true)

    if (!declaration) {
      setFieldErrors(nextFieldErrors)
      setError('Wymagane jest oświadczenie o posiadaniu numeru PWZFz.')
      return
    }

    if (
      nextFieldErrors.firstName ||
      nextFieldErrors.lastName ||
      nextFieldErrors.email ||
      nextFieldErrors.phone ||
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
      const recaptcha_token = await executeRecaptcha('register')
      const result = await register({
        email: email.trim(),
        password,
        recaptcha_token,
        first_name: firstName.trim(),
        last_name: lastName.trim(),
        pwzf_number: normalizePwzf(pwzf),
        pwzf_declaration: true,
        phone: formatPhoneForApi(phoneNational, countryCode) || undefined,
        qualification_level: qualificationLevel,
      })
      if (result.kind === 'needs_email_verification') {
        navigate(`/verify-email?email=${encodeURIComponent(result.email)}`, { replace: true })
        return
      }
      navigate('/', { replace: true })
    } catch (err) {
      handleRegisterError(err)
    } finally {
      setLoading(false)
    }
  }

  async function onGoogleCredential(credential: string) {
    const claims = parseGoogleIdTokenClaims(credential)
    const nextEmail = claims.email?.trim() || email.trim()
    const nextFirst = claims.first_name?.trim() || firstName.trim()
    const nextLast = claims.last_name?.trim() || lastName.trim()

    setEmail(nextEmail)
    setFirstName(nextFirst)
    setLastName(nextLast)
    setGoogleDraft({
      credential,
      email: nextEmail || undefined,
      first_name: nextFirst || undefined,
      last_name: nextLast || undefined,
    })
    setSubmitted(false)
    setFieldErrors({})
    setError(null)
    setInfoMessage(
      'Konto Google połączone. Uzupełnij numer PWZFz oraz oświadczenie, aby utworzyć konto.',
    )
  }

  function handleGoogleError(message: string) {
    if (/anulowane/i.test(message)) {
      toast.info(message)
    } else {
      toast.error(message)
    }
  }

  return (
    <div className="auth-form">
      <header className="auth-form__header">
        <h1>Rejestracja fizjoterapeuty</h1>
        <p>
          {googleMode
            ? 'E-mail wczytany z Google. Sprawdź lub popraw imię i nazwisko oraz uzupełnij numer PWZFz.'
            : 'Konto z numerem PWZFz - dostęp do panelu gabinetu.'}
        </p>
      </header>

      <form className="auth-form__body" onSubmit={onSubmit} noValidate>
        <div className="auth-form__row">
          <Field
            label="Imię"
            name="first_name"
            autoComplete="given-name"
            required
            value={firstName}
            onChange={(e) => {
              setFirstName(e.target.value)
              if (fieldErrors.firstName) {
                setFieldErrors((prev) => ({ ...prev, firstName: undefined }))
              }
            }}
            error={fieldErrors.firstName}
          />
          <Field
            label="Nazwisko"
            name="last_name"
            autoComplete="family-name"
            required
            value={lastName}
            onChange={(e) => {
              setLastName(e.target.value)
              if (fieldErrors.lastName) {
                setFieldErrors((prev) => ({ ...prev, lastName: undefined }))
              }
            }}
            error={fieldErrors.lastName}
          />
        </div>
        <Field
          label="E-mail"
          name="email"
          type="email"
          autoComplete="email"
          required={!googleMode}
          value={email}
          disabled={googleMode}
          onChange={(e) => {
            setEmail(e.target.value)
            if (fieldErrors.email) {
              setFieldErrors((prev) => ({ ...prev, email: undefined }))
            }
          }}
          error={fieldErrors.email}
        />
        <PhoneField
          countryCode={countryCode}
          nationalNumber={phoneNational}
          onCountryChange={(code) => {
            setCountryCode(code)
            if (fieldErrors.phone) {
              setFieldErrors((prev) => ({ ...prev, phone: undefined }))
            }
          }}
          onNationalNumberChange={(value) => {
            setPhoneNational(value)
            if (fieldErrors.phone) {
              setFieldErrors((prev) => ({ ...prev, phone: undefined }))
            }
          }}
          error={fieldErrors.phone}
          hint={
            googleMode
              ? 'Opcjonalnie - Google zwykle nie przekazuje telefonu, możesz dodać go tutaj.'
              : 'Opcjonalnie. Wybierz kraj, żeby ustawić prefix numeru.'
          }
        />
        <Field
          label="Numer PWZFz"
          name="pwzf_number"
          required
          inputMode="numeric"
          maxLength={20}
          value={pwzf}
          onChange={(e) => {
            setPwzf(e.target.value)
            if (fieldErrors.pwzf) {
              setFieldErrors((prev) => ({ ...prev, pwzf: undefined }))
            }
          }}
          error={fieldErrors.pwzf}
        />
        <div className="ui-field">
          <span className="ui-field__label">Tytuł zawodowy / Wykształcenie</span>
          <div className="qualification-grid" role="radiogroup" aria-label="Tytuł zawodowy">
            {QUALIFICATION_TILES.map((tile) => {
              const isSelected = qualificationLevel === tile.value
              return (
                <button
                  key={tile.value}
                  type="button"
                  role="radio"
                  aria-checked={isSelected}
                  className={`qualification-tile ${isSelected ? 'qualification-tile--selected' : ''}`}
                  onClick={() => setQualificationLevel(tile.value)}
                >
                  <span className="qualification-tile__title">{tile.title}</span>
                  <span className="qualification-tile__sub">{tile.sub}</span>
                </button>
              )
            })}
          </div>
        </div>

        {!googleMode ? (
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
        ) : null}

        <label className="auth-form__check">
          <input
            type="checkbox"
            checked={declaration}
            onChange={(e) => setDeclaration(e.target.checked)}
          />
          <span>Oświadczam, że posiadam ważne prawo wykonywania zawodu (PWZFz).</span>
        </label>

        <p className="auth-form__legal">
          Rejestrując konto, akceptujesz przetwarzanie danych zgodnie z{' '}
          <Link to="/privacy">Polityką prywatności</Link> oraz{' '}
          <Link to="/cookies">Polityką cookies</Link>.
        </p>

        {infoMessage ? (
          <p className="auth-form__info" role="status">
            {infoMessage}
          </p>
        ) : null}

        {error ? (
          <p className="auth-form__error" role="alert">
            {error}
          </p>
        ) : null}

        <Button type="submit" loading={loading} className="auth-form__submit">
          {googleMode ? 'Dokończ rejestrację Google' : 'Utwórz konto'}
        </Button>
      </form>

      {!googleMode && isWebGoogleSignInConfigured() ? (
        <GoogleSignInButton
          disabled={loading}
          title="Zarejestruj przez Google"
          hint="Kliknij Google - e-mail, imię i nazwisko uzupełnią się same. Potem podaj tylko PWZFz i oświadczenie."
          onCredential={onGoogleCredential}
          onError={handleGoogleError}
        />
      ) : null}

      <p className="auth-form__footer">
        Masz już konto? <Link to="/login">Zaloguj się</Link>
        <span aria-hidden="true">·</span>
        <Link to="/privacy">Prywatność</Link>
      </p>
    </div>
  )
}
