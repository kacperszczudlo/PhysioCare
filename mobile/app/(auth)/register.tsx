import { Link, useRouter } from 'expo-router'
import { useMemo, useState } from 'react'
import { Pressable, StyleSheet, Text, View } from 'react-native'

import { getErrorMessage, getFieldError } from '@/api/client'
import { useAuth } from '@/auth/AuthContext'
import { Button } from '@/components/Button'
import { Field } from '@/components/Field'
import { KeyboardAwareForm } from '@/components/KeyboardAwareForm'
import { PasswordRequirements } from '@/components/PasswordRequirements'
import { getEmailError } from '@/lib/emailPolicy'
import { getFirstNameError, getLastNameError } from '@/lib/fieldPolicy'
import {
  getPasswordError,
  getPasswordRequirements,
  PASSWORD_MESSAGES,
  passwordsMatch,
} from '@/lib/passwordPolicy'
import { colors, radius, space, typography } from '@/theme/tokens'

export default function RegisterScreen() {
  const { register } = useAuth()
  const router = useRouter()

  const [firstName, setFirstName] = useState('')
  const [lastName, setLastName] = useState('')
  const [email, setEmail] = useState('')
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
    password?: string
    confirmPassword?: string
    therapistId?: string
  }>({})
  const [passwordTouched, setPasswordTouched] = useState(false)
  const [submitted, setSubmitted] = useState(false)
  const [loading, setLoading] = useState(false)

  const passwordHints = { email, firstName, lastName }
  const passwordRequirements = getPasswordRequirements(password, passwordHints)
  const showRequirementErrors = submitted || passwordTouched

  const canSubmit = useMemo(
    () =>
      terms &&
      medical &&
      firstName.trim() &&
      lastName.trim() &&
      email.trim() &&
      password.length > 0 &&
      confirmPassword.length > 0 &&
      therapistId.trim(),
    [terms, medical, firstName, lastName, email, password, confirmPassword, therapistId],
  )

  async function onSubmit() {
    setSubmitted(true)
    setError(null)

    if (!terms || !medical) {
      setError('Uzupełnij formularz i zaznacz wymagane zgody RODO.')
      return
    }

    const nextFieldErrors: {
      firstName?: string
      lastName?: string
      email?: string
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
      await register({
        email: email.trim(),
        password,
        first_name: firstName.trim(),
        last_name: lastName.trim(),
        therapist_id: therapistId.trim(),
        consents: { terms, medical_data: medical },
      })
      router.replace('/(tabs)')
    } catch (err) {
      const apiFirstNameError = getFieldError(err, 'first_name')
      const apiLastNameError = getFieldError(err, 'last_name')
      const apiEmailError = getFieldError(err, 'email')
      const apiPasswordError = getFieldError(err, 'password')
      const apiTherapistError = getFieldError(err, 'therapist_id')
      if (
        apiFirstNameError ||
        apiLastNameError ||
        apiEmailError ||
        apiPasswordError ||
        apiTherapistError
      ) {
        setFieldErrors({
          firstName: apiFirstNameError ?? undefined,
          lastName: apiLastNameError ?? undefined,
          email: apiEmailError ?? undefined,
          password: apiPasswordError ?? undefined,
          therapistId: apiTherapistError ?? undefined,
        })
      }
      const message = getErrorMessage(err, 'Rejestracja nie powiodła się.')
      const duplicate =
        (apiEmailError && message === apiEmailError) ||
        (apiPasswordError && message === apiPasswordError)
      setError(duplicate ? null : message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <KeyboardAwareForm style={styles.flex} contentContainerStyle={styles.container}>
      <Text style={styles.brand}>PhysioCare</Text>
      <Text style={styles.title}>Rejestracja pacjenta</Text>
      <Text style={styles.subtitle}>
        Załóż konto i zaakceptuj wymagane zgody, aby korzystać z zaleceń terapeuty.
      </Text>

      <View style={styles.form}>
        <Field
          label="Imię"
          value={firstName}
          onChangeText={(value) => {
            setFirstName(value)
            if (fieldErrors.firstName) {
              setFieldErrors((prev) => ({ ...prev, firstName: undefined }))
            }
          }}
          autoComplete="given-name"
          error={fieldErrors.firstName}
        />
        <Field
          label="Nazwisko"
          value={lastName}
          onChangeText={(value) => {
            setLastName(value)
            if (fieldErrors.lastName) {
              setFieldErrors((prev) => ({ ...prev, lastName: undefined }))
            }
          }}
          autoComplete="family-name"
          error={fieldErrors.lastName}
        />
        <Field
          label="E-mail"
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
          error={fieldErrors.email}
        />
        <Field
          label="Hasło"
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
          label="Powtórz hasło"
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
        <Field
          label="Kod terapeuty"
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
          hint="Kod z panelu webowego terapeuty: Profil → „Kod dla pacjenta” (Kopiuj kod)."
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

        {error ? (
          <Text style={styles.error} accessibilityRole="alert">
            {error}
          </Text>
        ) : null}

        <Button
          title="Utwórz konto"
          loading={loading}
          disabled={!canSubmit}
          onPress={() => void onSubmit()}
        />
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
    fontSize: typography.xl,
    fontWeight: '800',
    color: colors.primary,
    marginTop: space['2xl'],
  },
  title: { fontSize: typography['2xl'], fontWeight: '700', color: colors.ink },
  subtitle: { fontSize: typography.sm, color: colors.muted, marginBottom: space.sm },
  form: { gap: space.base },
  error: { color: colors.danger, fontSize: typography.sm },
  link: {
    color: colors.primary,
    fontWeight: '600',
    textAlign: 'center',
    marginTop: space.base,
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
