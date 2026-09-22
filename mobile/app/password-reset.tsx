/**
 * @file password-reset.tsx
 * @description Ekran wielokrokowego procesu resetowania hasła (żądanie kodu, weryfikacja kodu 6-cyfrowego, zmiana hasła).
 */

import { Link, useLocalSearchParams, useRouter, type Href } from 'expo-router'
import { useState } from 'react'
import { StyleSheet, Text, View } from 'react-native'

import { ApiError, getErrorMessage, getFieldError } from '@/api/client'
import { useAuth } from '@/auth/AuthContext'
import { ErrorBanner, SuccessBanner } from '@/components/AsyncState'
import { BrandMark } from '@/components/BrandMark'
import { Button } from '@/components/Button'
import { Field } from '@/components/Field'
import { KeyboardAwareForm } from '@/components/KeyboardAwareForm'
import { PasswordRequirements } from '@/components/PasswordRequirements'
import { getEmailError } from '@/lib/emailPolicy'
import {
  getPasswordError,
  getPasswordRequirements,
  PASSWORD_MESSAGES,
  passwordsMatch,
} from '@/lib/passwordPolicy'
import { colors, space, typography } from '@/theme/tokens'

/** Krok w formularzu resetu hasła. */
type Step = 'request' | 'code' | 'password'

function firstParam(value: string | string[] | undefined): string {
  if (Array.isArray(value)) {
    return (value[0] ?? '').trim()
  }
  return (value ?? '').trim()
}

/**
 * Ekran resetu/odzyskiwania hasła z trzyetapowym procesem weryfikacji dwuskładnikowej przez e-mail.
 *
 * @returns Element React Native prezentujący ekran resetowania hasła.
 */
export default function PasswordResetScreen() {
  const {
    requestPasswordReset,
    verifyPasswordResetCode,
    confirmPasswordReset,
    logout,
    isAuthenticated,
  } = useAuth()
  const router = useRouter()
  const params = useLocalSearchParams<{ email?: string | string[] }>()
  const emailFromParams = firstParam(params.email)

  const [step, setStep] = useState<Step>('request')
  const [email, setEmail] = useState(emailFromParams)
  const [code, setCode] = useState('')
  const [resetToken, setResetToken] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [message, setMessage] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [emailError, setEmailError] = useState<string | null>(null)
  const [codeError, setCodeError] = useState<string | null>(null)
  const [passwordError, setPasswordError] = useState<string | null>(null)
  const [confirmPasswordError, setConfirmPasswordError] = useState<string | null>(null)
  const [passwordTouched, setPasswordTouched] = useState(false)
  const [loading, setLoading] = useState(false)

  const passwordRequirements = getPasswordRequirements(password)

  function goToRequest() {
    setStep('request')
    setCode('')
    setResetToken('')
    setPassword('')
    setConfirmPassword('')
    setMessage(null)
    setError(null)
    setCodeError(null)
    setPasswordError(null)
    setConfirmPasswordError(null)
    setPasswordTouched(false)
  }

  function goToCodeStep(notice?: string | null) {
    setStep('code')
    setCode('')
    setResetToken('')
    setPassword('')
    setConfirmPassword('')
    setPasswordTouched(false)
    setCodeError(null)
    setPasswordError(null)
    setConfirmPasswordError(null)
    setError(null)
    setMessage(notice ?? null)
  }

  async function onRequest() {
    setError(null)
    setMessage(null)
    const localEmailError = getEmailError(email)
    if (localEmailError) {
      setEmailError(localEmailError)
      return
    }
    setEmailError(null)
    setLoading(true)
    try {
      const detail = await requestPasswordReset(email.trim())
      goToCodeStep(detail)
    } catch (err) {
      const apiEmailError = getFieldError(err, 'email')
      if (apiEmailError) {
        setEmailError(apiEmailError)
        setError(null)
      } else {
        setError(getErrorMessage(err, 'Nie udało się wysłać kodu.'))
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
      setError(getErrorMessage(err, 'Nie udało się wysłać kodu ponownie.'))
    } finally {
      setLoading(false)
    }
  }

  async function onVerifyCode() {
    setError(null)
    setMessage(null)
    const cleaned = code.trim()
    if (!/^\d{6}$/.test(cleaned)) {
      setCodeError('Wpisz 6-cyfrowy kod z e-maila.')
      return
    }
    setCodeError(null)
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
        setCodeError(apiCodeError)
        setError(null)
      } else {
        setError(getErrorMessage(err, 'Nie udało się zweryfikować kodu.'))
      }
    } finally {
      setLoading(false)
    }
  }

  async function onSetPassword() {
    setError(null)
    setMessage(null)
    setPasswordTouched(true)

    const localPasswordError = getPasswordError(password)
    if (localPasswordError) {
      setPasswordError(localPasswordError)
      setConfirmPasswordError(null)
      return
    }
    if (!passwordsMatch(password, confirmPassword)) {
      setPasswordError(null)
      setConfirmPasswordError(PASSWORD_MESSAGES.mismatch)
      return
    }
    if (!resetToken) {
      goToCodeStep('Sesja resetu wygasła. Wyślij kod ponownie.')
      return
    }
    setPasswordError(null)
    setConfirmPasswordError(null)
    setLoading(true)
    try {
      await confirmPasswordReset({
        reset_token: resetToken,
        new_password: password,
        new_password_confirm: confirmPassword,
      })
      if (isAuthenticated) {
        await logout()
      }
      const q = new URLSearchParams({
        reset: '1',
        email: email.trim(),
      })
      router.replace(`/(auth)/login?${q.toString()}` as Href)
    } catch (err) {
      const apiPasswordError = getFieldError(err, 'new_password') ?? getFieldError(err, 'password')
      if (apiPasswordError) {
        setPasswordError(apiPasswordError)
        setError(null)
        return
      }
      if (err instanceof ApiError && err.code === 'AUTH_028') {
        goToCodeStep(`${err.message} Wyślij kod ponownie.`)
        return
      }
      setError(getErrorMessage(err, 'Nie udało się ustawić hasła.'))
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
    <KeyboardAwareForm style={styles.flex} contentContainerStyle={styles.container}>
      <BrandMark variant="logo" size="sm" style={styles.brand} />
      <Text style={styles.title}>{title}</Text>
      <Text style={styles.subtitle}>{subtitle}</Text>

      <View style={styles.form}>
        {step === 'code' ? (
          <>
            <Field
              label="Kod z e-maila"
              value={code}
              onChangeText={(value) => {
                setCode(value.replace(/\D/g, '').slice(0, 6))
                if (codeError) {
                  setCodeError(null)
                }
              }}
              keyboardType="number-pad"
              autoComplete="one-time-code"
              error={codeError}
            />
            <Button title="Potwierdź kod" loading={loading} onPress={() => void onVerifyCode()} />
            <Button
              title="Wyślij kod ponownie"
              variant="secondary"
              disabled={loading}
              onPress={() => void onResendCode()}
            />
            <Button
              title="Zmień e-mail"
              variant="secondary"
              disabled={loading}
              onPress={goToRequest}
            />
          </>
        ) : step === 'password' ? (
          <>
            <Field
              label="Nowe hasło"
              value={password}
              onChangeText={(value) => {
                setPassword(value)
                if (passwordError) {
                  setPasswordError(null)
                }
              }}
              onBlur={() => setPasswordTouched(true)}
              secureTextEntry
              error={passwordError}
            />
            <PasswordRequirements
              requirements={passwordRequirements}
              showErrors={passwordTouched || Boolean(passwordError)}
            />
            <Field
              label="Powtórz hasło"
              value={confirmPassword}
              onChangeText={(value) => {
                setConfirmPassword(value)
                if (confirmPasswordError) {
                  setConfirmPasswordError(null)
                }
              }}
              secureTextEntry
              error={confirmPasswordError}
            />
            <Button
              title="Ustaw nowe hasło"
              loading={loading}
              onPress={() => void onSetPassword()}
            />
            <Button
              title="Wyślij kod ponownie"
              variant="secondary"
              disabled={loading}
              onPress={() => void onResendCode()}
            />
          </>
        ) : (
          <>
            <Field
              label="E-mail"
              value={email}
              onChangeText={(value) => {
                setEmail(value)
                if (emailError) {
                  setEmailError(null)
                }
              }}
              autoCapitalize="none"
              keyboardType="email-address"
              autoComplete="email"
              error={emailError}
            />
            <Button
              title="Wyślij kod na e-mail"
              loading={loading}
              onPress={() => void onRequest()}
            />
          </>
        )}

        {message ? <SuccessBanner message={message} /> : null}
        {error ? <ErrorBanner message={error} /> : null}
      </View>

      <Link href="/(auth)/login" style={styles.link}>
        Powrót do logowania
      </Link>
    </KeyboardAwareForm>
  )
}

const styles = StyleSheet.create({
  flex: { flex: 1, backgroundColor: colors.bg },
  container: {
    flexGrow: 1,
    padding: space.xl,
    paddingTop: space['4xl'],
    paddingBottom: space['4xl'],
    gap: space.md,
  },
  brand: { marginBottom: space.sm, alignSelf: 'center', alignItems: 'center' },
  title: { fontSize: typography['2xl'], fontWeight: '700', color: colors.ink },
  subtitle: { fontSize: typography.sm, color: colors.muted, marginBottom: space.sm },
  form: { gap: space.base },
  link: {
    color: colors.primary,
    fontWeight: '600',
    textAlign: 'center',
    marginTop: space.base,
    textDecorationLine: 'underline',
  },
})
