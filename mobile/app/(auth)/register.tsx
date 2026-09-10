import { Link, useRouter, type Href } from 'expo-router'
import { useEffect, useMemo, useState } from 'react'
import { Pressable, StyleSheet, Text, View } from 'react-native'

import { getErrorMessage, getFieldError } from '@/api/client'
import { useAuth } from '@/auth/AuthContext'
import {
  peekGoogleRegistrationDraft,
  takeGoogleRegistrationDraft,
  type GoogleRegistrationDraft,
} from '@/auth/googleRegistrationDraft'
import { GoogleSignInButton, isGoogleSignInConfigured } from '@/auth/googleSignIn'
import { parseGoogleIdTokenClaims } from '@/auth/parseGoogleIdToken'
import { BrandMark } from '@/components/BrandMark'
import { Button } from '@/components/Button'
import { Field } from '@/components/Field'
import { KeyboardAwareForm } from '@/components/KeyboardAwareForm'
import { PasswordRequirements } from '@/components/PasswordRequirements'
import { PhoneField } from '@/components/PhoneField'
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
import { colors, radius, space, typography } from '@/theme/tokens'

export default function RegisterScreen() {
  const { register } = useAuth()
  const router = useRouter()

  const [googleDraft, setGoogleDraft] = useState<GoogleRegistrationDraft | null>(() =>
    peekGoogleRegistrationDraft(),
  )
  const [firstName, setFirstName] = useState(() => peekGoogleRegistrationDraft()?.first_name ?? '')
  const [lastName, setLastName] = useState(() => peekGoogleRegistrationDraft()?.last_name ?? '')
  const [email, setEmail] = useState(() => peekGoogleRegistrationDraft()?.email ?? '')
  const [countryCode, setCountryCode] = useState(DEFAULT_COUNTRY_CODE)
  const [phoneNational, setPhoneNational] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [therapistId, setTherapistId] = useState('')
  const [terms, setTerms] = useState(false)
  const [medical, setMedical] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [fieldErrors, setFieldErrors] = useState<{
    firstName?: string
    lastName?: string
    email?: string
    phone?: string
    password?: string
    confirmPassword?: string
    therapistId?: string
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
    setError(
      'Dane z Google (e-mail, imię, nazwisko) są uzupełnione. Podaj kod terapeuty i zaznacz zgody — telefon opcjonalnie.',
    )
  }, [])

  const canSubmit = useMemo(() => {
    if (!(terms && medical && therapistId.trim())) {
      return false
    }
    if (!(firstName.trim() && lastName.trim())) {
      return false
    }
    if (googleMode) {
      return true
    }
    return Boolean(email.trim() && password.length > 0 && confirmPassword.length > 0)
  }, [
    terms,
    medical,
    therapistId,
    googleMode,
    firstName,
    lastName,
    email,
    password,
    confirmPassword,
  ])

  async function finishGoogleRegistration(credential: string) {
    if (!validateGoogleRegistrationFields()) {
      return
    }

    setFieldErrors({})
    setLoading(true)
    try {
      const result = await register({
        google_credential: credential,
        first_name: firstName.trim(),
        last_name: lastName.trim(),
        therapist_id: therapistId.trim(),
        phone: formatPhoneForApi(phoneNational, countryCode) || undefined,
        consents: { terms, medical_data: medical },
      })
      setGoogleDraft(null)
      if (result.kind === 'needs_email_verification') {
        router.replace(
          `/(auth)/verify-email?email=${encodeURIComponent(result.email)}` as Href,
        )
        return
      }
      router.replace('/(tabs)')
    } catch (err) {
      handleRegisterError(err)
    } finally {
      setLoading(false)
    }
  }

  function validateGoogleRegistrationFields(): boolean {
    if (!terms || !medical) {
      setError('Zaznacz wymagane zgody RODO, żeby dokończyć rejestrację Google.')
      return false
    }

    const nextFieldErrors: {
      firstName?: string
      lastName?: string
      phone?: string
      therapistId?: string
    } = {}
    const firstNameError = getFirstNameError(firstName)
    if (firstNameError) {
      nextFieldErrors.firstName = firstNameError
    }
    const lastNameError = getLastNameError(lastName)
    if (lastNameError) {
      nextFieldErrors.lastName = lastNameError
    }
    const phoneError = getPhoneError(phoneNational, countryCode)
    if (phoneError) {
      nextFieldErrors.phone = phoneError
    }
    if (!therapistId.trim()) {
      nextFieldErrors.therapistId = 'Podaj kod terapeuty.'
    } else if (
      !/^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i.test(
        therapistId.trim(),
      )
    ) {
      nextFieldErrors.therapistId = 'Podaj prawidłowy kod terapeuty (UUID z panelu terapeuty).'
    }
    if (
      nextFieldErrors.firstName ||
      nextFieldErrors.lastName ||
      nextFieldErrors.phone ||
      nextFieldErrors.therapistId
    ) {
      setFieldErrors((prev) => ({ ...prev, ...nextFieldErrors }))
      setError('Uzupełnij kod terapeuty i zgody (oraz imię/nazwisko, jeśli Google ich nie podało).')
      return false
    }
    return true
  }

  async function onSubmit() {
    setSubmitted(true)
    setError(null)

    if (googleMode && googleDraft?.credential) {
      await finishGoogleRegistration(googleDraft.credential)
      return
    }

    if (!terms || !medical) {
      setError('Uzupełnij formularz i zaznacz wymagane zgody RODO.')
      return
    }

    const nextFieldErrors: {
      firstName?: string
      lastName?: string
      email?: string
      phone?: string
      password?: string
      confirmPassword?: string
      therapistId?: string
    } = {}
    const firstNameError = getFirstNameError(firstName)
    if (firstNameError) {
      nextFieldErrors.firstName = firstNameError
    }
    const lastNameError = getLastNameError(lastName)
    if (lastNameError) {
      nextFieldErrors.lastName = lastNameError
    }
    const emailError = getEmailError(email)
    if (emailError) {
      nextFieldErrors.email = emailError
    }
    const phoneError = getPhoneError(phoneNational, countryCode)
    if (phoneError) {
      nextFieldErrors.phone = phoneError
    }
    const passwordError = getPasswordError(password, passwordHints)
    if (passwordError) {
      nextFieldErrors.password = passwordError
    }
    if (!passwordsMatch(password, confirmPassword)) {
      nextFieldErrors.confirmPassword = PASSWORD_MESSAGES.mismatch
    }
    if (!therapistId.trim()) {
      nextFieldErrors.therapistId = 'Podaj kod terapeuty.'
    } else if (
      !/^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i.test(
        therapistId.trim(),
      )
    ) {
      nextFieldErrors.therapistId = 'Podaj prawidłowy kod terapeuty (UUID z panelu terapeuty).'
    }

    if (
      nextFieldErrors.firstName ||
      nextFieldErrors.lastName ||
      nextFieldErrors.email ||
      nextFieldErrors.phone ||
      nextFieldErrors.password ||
      nextFieldErrors.confirmPassword ||
      nextFieldErrors.therapistId
    ) {
      setFieldErrors(nextFieldErrors)
      return
    }

    setFieldErrors({})
    setLoading(true)
    try {
      const result = await register({
        email: email.trim(),
        password,
        first_name: firstName.trim(),
        last_name: lastName.trim(),
        therapist_id: therapistId.trim(),
        phone: formatPhoneForApi(phoneNational, countryCode) || undefined,
        consents: { terms, medical_data: medical },
      })
      if (result.kind === 'needs_email_verification') {
        router.replace(
          `/(auth)/verify-email?email=${encodeURIComponent(result.email)}` as Href,
        )
        return
      }
      router.replace('/(tabs)')
    } catch (err) {
      handleRegisterError(err)
    } finally {
      setLoading(false)
    }
  }

  function handleRegisterError(err: unknown) {
    const apiFirstNameError = getFieldError(err, 'first_name')
    const apiLastNameError = getFieldError(err, 'last_name')
    const apiEmailError = getFieldError(err, 'email')
    const apiPhoneError = getFieldError(err, 'phone')
    const apiPasswordError = getFieldError(err, 'password')
    const apiTherapistError = getFieldError(err, 'therapist_id')
    const apiGoogleError = getFieldError(err, 'google_credential')
    if (
      apiFirstNameError ||
      apiLastNameError ||
      apiEmailError ||
      apiPhoneError ||
      apiPasswordError ||
      apiTherapistError
    ) {
      setFieldErrors({
        firstName: apiFirstNameError ?? undefined,
        lastName: apiLastNameError ?? undefined,
        email: apiEmailError ?? undefined,
        phone: apiPhoneError ?? undefined,
        password: apiPasswordError ?? undefined,
        therapistId: apiTherapistError ?? undefined,
      })
    }

    const accountExists =
      Boolean(apiEmailError && /już zarejestrowany/i.test(apiEmailError)) ||
      Boolean(apiGoogleError && /już istnieje/i.test(apiGoogleError))

    if (accountExists) {
      setGoogleDraft(null)
      setError(
        apiEmailError ||
          apiGoogleError ||
          'Ten adres e-mail jest już zarejestrowany. Użyj logowania zamiast rejestracji.',
      )
      return
    }

    const message =
      apiGoogleError || getErrorMessage(err, 'Rejestracja nie powiodła się.')
    const duplicate =
      (apiEmailError && message === apiEmailError) ||
      (apiPasswordError && message === apiPasswordError)
    setError(duplicate ? null : message)
  }

  async function onGoogleSuccess(idToken: string) {
    setSubmitted(false)
    setError(null)
    const claims = parseGoogleIdTokenClaims(idToken)
    const nextEmail = claims.email?.trim() || email.trim()
    const nextFirst = claims.first_name?.trim() || firstName.trim()
    const nextLast = claims.last_name?.trim() || lastName.trim()

    setEmail(nextEmail)
    setFirstName(nextFirst)
    setLastName(nextLast)
    setGoogleDraft({
      credential: idToken,
      email: nextEmail || undefined,
      first_name: nextFirst || undefined,
      last_name: nextLast || undefined,
    })
    setFieldErrors({})
    setError(
      nextFirst && nextLast && nextEmail
        ? 'Dane z Google zapisane. Został kod terapeuty i zgody (telefon opcjonalnie).'
        : 'Konto Google połączone. Uzupełnij brakujące imię/nazwisko, kod terapeuty i zgody.',
    )
  }

  return (
    <KeyboardAwareForm style={styles.flex} contentContainerStyle={styles.container}>
      <BrandMark variant="logo" size="md" style={styles.brand} />
      <Text style={styles.title}>Rejestracja pacjenta</Text>
      <Text style={styles.subtitle}>
        {googleMode
          ? 'E-mail, imię i nazwisko z Google. Uzupełnij kod terapeuty i zgody (telefon opcjonalnie).'
          : 'Załóż konto i zaakceptuj wymagane zgody, aby korzystać z zaleceń terapeuty.'}
      </Text>

      <View style={styles.form}>
        <Field
          label="Imię *"
          value={firstName}
          onChangeText={(value) => {
            setFirstName(value)
            if (fieldErrors.firstName) {
              setFieldErrors((prev) => ({ ...prev, firstName: undefined }))
            }
          }}
          autoComplete="given-name"
          editable={!(googleMode && Boolean(firstName.trim()))}
          error={fieldErrors.firstName}
        />
        <Field
          label="Nazwisko *"
          value={lastName}
          onChangeText={(value) => {
            setLastName(value)
            if (fieldErrors.lastName) {
              setFieldErrors((prev) => ({ ...prev, lastName: undefined }))
            }
          }}
          autoComplete="family-name"
          editable={!(googleMode && Boolean(lastName.trim()))}
          error={fieldErrors.lastName}
        />
        <Field
          label={googleMode ? 'E-mail (z Google)' : 'E-mail *'}
          value={email}
          onChangeText={(value) => {
            setEmail(value)
            if (fieldErrors.email) {
              setFieldErrors((prev) => ({ ...prev, email: undefined }))
            }
          }}
          autoCapitalize="none"
          keyboardType="email-address"
          autoComplete="email"
          editable={!googleMode}
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
              ? 'Opcjonalnie — Google zwykle nie przekazuje telefonu, możesz dodać go tutaj.'
              : 'Opcjonalnie. Wybierz kraj, żeby ustawić prefix numeru.'
          }
        />
        {!googleMode ? (
          <>
            <Field
              label="Hasło *"
              value={password}
              onChangeText={(value) => {
                setPassword(value)
                if (fieldErrors.password) {
                  setFieldErrors((prev) => ({ ...prev, password: undefined }))
                }
              }}
              onBlur={() => setPasswordTouched(true)}
              secureTextEntry
              autoComplete="new-password"
              error={fieldErrors.password}
            />
            <PasswordRequirements
              requirements={passwordRequirements}
              showErrors={showRequirementErrors}
            />
            <Field
              label="Powtórz hasło *"
              value={confirmPassword}
              onChangeText={(value) => {
                setConfirmPassword(value)
                if (fieldErrors.confirmPassword) {
                  setFieldErrors((prev) => ({ ...prev, confirmPassword: undefined }))
                }
              }}
              secureTextEntry
              autoComplete="new-password"
              error={fieldErrors.confirmPassword}
            />
          </>
        ) : null}
        <Field
          label="Kod terapeuty *"
          value={therapistId}
          onChangeText={(value) => {
            setTherapistId(value)
            if (fieldErrors.therapistId) {
              setFieldErrors((prev) => ({ ...prev, therapistId: undefined }))
            }
          }}
          autoCapitalize="none"
          autoCorrect={false}
          error={fieldErrors.therapistId}
          hint="Kod z panelu webowego terapeuty: Profil / „Kod dla pacjenta” (Kopiuj kod)."
        />

        <ConsentToggle
          label="Akceptuję regulamin serwisu (wymagane)"
          checked={terms}
          onToggle={() => setTerms((v) => !v)}
        />
        <ConsentToggle
          label="Wyrażam zgodę na przetwarzanie danych medycznych (wymagane)"
          checked={medical}
          onToggle={() => setMedical((v) => !v)}
        />
        <Text style={styles.legalHint}>
          Szczegóły przetwarzania danych:{' '}
          <Link href="/legal/privacy" style={styles.inlineLink}>
            Polityka prywatności
          </Link>
          {' · '}
          <Link href="/legal/cookies" style={styles.inlineLink}>
            Cookies
          </Link>
        </Text>

        {error ? (
          <Text style={styles.error} accessibilityRole="alert">
            {error}
          </Text>
        ) : null}

        <Button
          title={googleMode ? 'Dokończ rejestrację Google' : 'Utwórz konto'}
          loading={loading}
          disabled={!canSubmit}
          onPress={() => void onSubmit()}
        />

        {!googleMode && isGoogleSignInConfigured ? (
          <GoogleSignInButton
            loading={loading}
          title="Zarejestruj przez Google"
          hint="Kliknij Google — e-mail, imię i nazwisko uzupełnią się same. Potem podaj kod terapeuty i zgody."
          onSuccess={onGoogleSuccess}
            onError={setError}
          />
        ) : null}
      </View>

      <Link href="/(auth)/login" style={styles.link}>
        Mam już konto - zaloguj się
      </Link>
    </KeyboardAwareForm>
  )
}

function ConsentToggle({
  label,
  checked,
  onToggle,
}: {
  label: string
  checked: boolean
  onToggle: () => void
}) {
  return (
    <Pressable
      onPress={onToggle}
      style={styles.consentRow}
      accessibilityRole="checkbox"
      accessibilityState={{ checked }}
    >
      <View style={[styles.checkbox, checked ? styles.checkboxOn : null]}>
        {checked ? <Text style={styles.checkMark}>✓</Text> : null}
      </View>
      <Text style={styles.consentLabel}>{label}</Text>
    </Pressable>
  )
}

const styles = StyleSheet.create({
  flex: { flex: 1, backgroundColor: colors.bg },
  container: { padding: space.xl, gap: space.md, paddingBottom: space['4xl'] },
  brand: {
    marginTop: space['2xl'],
    alignSelf: 'center',
    alignItems: 'center',
  },
  title: { fontSize: typography['2xl'], fontWeight: '700', color: colors.ink },
  subtitle: { fontSize: typography.sm, color: colors.muted, marginBottom: space.sm },
  form: { gap: space.base },
  error: { color: colors.danger, fontSize: typography.sm },
  legalHint: { fontSize: typography.sm, color: colors.muted, lineHeight: 20 },
  inlineLink: { color: colors.primary, fontWeight: '600', textDecorationLine: 'underline' },
  link: {
    color: colors.primary,
    fontWeight: '600',
    textAlign: 'center',
    marginTop: space.base,
    textDecorationLine: 'underline',
  },
  consentRow: { flexDirection: 'row', gap: space.md, alignItems: 'flex-start' },
  checkbox: {
    width: 24,
    height: 24,
    borderRadius: radius.sm,
    borderWidth: 1.5,
    borderColor: colors.borderStrong,
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: 2,
    backgroundColor: colors.surface,
  },
  checkboxOn: {
    backgroundColor: colors.primary,
    borderColor: colors.primary,
  },
  checkMark: { color: colors.onPrimary, fontWeight: '700', fontSize: 14 },
  consentLabel: { flex: 1, color: colors.ink, fontSize: typography.sm, lineHeight: 20 },
})
