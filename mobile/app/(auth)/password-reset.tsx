import { Link } from 'expo-router'
import { useState } from 'react'
import { StyleSheet, Text, View } from 'react-native'

import { getErrorMessage, getFieldError } from '@/api/client'
import { useAuth } from '@/auth/AuthContext'
import { ErrorBanner, SuccessBanner } from '@/components/AsyncState'
import { Button } from '@/components/Button'
import { Field } from '@/components/Field'
import { KeyboardAwareForm } from '@/components/KeyboardAwareForm'
import { PasswordRequirements } from '@/components/PasswordRequirements'
import { getEmailError } from '@/lib/emailPolicy'
import { getPasswordError, getPasswordRequirements } from '@/lib/passwordPolicy'
import { colors, space, typography } from '@/theme/tokens'

export default function PasswordResetScreen() {
  const { requestPasswordReset, confirmPasswordReset } = useAuth()
  const [step, setStep] = useState<'request' | 'confirm'>('request')
  const [email, setEmail] = useState('')
  const [token, setToken] = useState('')
  const [password, setPassword] = useState('')
  const [message, setMessage] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [emailError, setEmailError] = useState<string | null>(null)
  const [passwordError, setPasswordError] = useState<string | null>(null)
  const [passwordTouched, setPasswordTouched] = useState(false)
  const [loading, setLoading] = useState(false)

  const passwordRequirements = getPasswordRequirements(password)

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
      setMessage(detail)
      setStep('confirm')
    } catch (err) {
      const apiEmailError = getFieldError(err, 'email')
      if (apiEmailError) {
        setEmailError(apiEmailError)
        setError(null)
      } else {
        setError(getErrorMessage(err, 'Nie udało się wysłać linku.'))
      }
    } finally {
      setLoading(false)
    }
  }

  async function onConfirm() {
    setError(null)
    setMessage(null)
    const localPasswordError = getPasswordError(password)
    if (localPasswordError) {
      setPasswordError(localPasswordError)
      setPasswordTouched(true)
      return
    }
    setPasswordError(null)
    setLoading(true)
    try {
      const detail = await confirmPasswordReset({
        token: token.trim(),
        new_password: password,
      })
      setMessage(detail)
    } catch (err) {
      const apiPasswordError =
        getFieldError(err, 'new_password') ?? getFieldError(err, 'password')
      if (apiPasswordError) {
        setPasswordError(apiPasswordError)
        setError(null)
      } else {
        setError(getErrorMessage(err, 'Nie udało się ustawić hasła.'))
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <KeyboardAwareForm style={styles.flex} contentContainerStyle={styles.container}>
      <Text style={styles.title}>Reset hasła</Text>
      <Text style={styles.subtitle}>
        {step === 'request'
          ? 'Wyślemy token resetu na e-mail (w trybie deweloperskim: konsola backendu).'
          : 'Wklej token z wiadomości i ustaw nowe hasło.'}
      </Text>

      <View style={styles.form}>
        {step === 'request' ? (
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
            <Button title="Wyślij token" loading={loading} onPress={() => void onRequest()} />
          </>
        ) : (
          <>
            <Field label="Token" value={token} onChangeText={setToken} autoCapitalize="none" />
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
            <Button title="Ustaw nowe hasło" loading={loading} onPress={() => void onConfirm()} />
            <Button title="Wróć do e-maila" variant="ghost" onPress={() => setStep('request')} />
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
  title: { fontSize: typography['2xl'], fontWeight: '700', color: colors.ink },
  subtitle: { fontSize: typography.sm, color: colors.muted, marginBottom: space.sm },
  form: { gap: space.base },
  link: {
    color: colors.primary,
    fontWeight: '600',
    textAlign: 'center',
    marginTop: space.base,
  },
})
