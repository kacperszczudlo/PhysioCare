import { Link, useLocalSearchParams, useRouter } from 'expo-router'
import { useState } from 'react'
import { StyleSheet, Text, View } from 'react-native'

import { getErrorMessage, getFieldError } from '@/api/client'
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

function firstParam(value: string | string[] | undefined): string {
  if (Array.isArray(value)) {
    return (value[0] ?? '').trim()
  }
  return (value ?? '').trim()
}

export default function PasswordResetScreen() {
  const { requestPasswordReset, confirmPasswordReset, logout, isAuthenticated } = useAuth()
  const router = useRouter()
  const params = useLocalSearchParams<{ token?: string | string[]; email?: string | string[] }>()
  const tokenFromLink = firstParam(params.token)
  const emailFromParams = firstParam(params.email)

  const [email, setEmail] = useState(emailFromParams)
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [message, setMessage] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [emailError, setEmailError] = useState<string | null>(null)
  const [passwordError, setPasswordError] = useState<string | null>(null)
  const [confirmPasswordError, setConfirmPasswordError] = useState<string | null>(null)
  const [passwordTouched, setPasswordTouched] = useState(false)
  const [loading, setLoading] = useState(false)

  const isConfirmMode = Boolean(tokenFromLink)
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
      await requestPasswordReset(email.trim())
      setMessage('Wysłaliśmy link resetujący. Sprawdź e-mail i kliknij link w wiadomości.')
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
    setPasswordTouched(true)

    if (!tokenFromLink) {
      setError('Użyj linku z wiadomości e-mail, aby ustawić nowe hasło.')
      return
    }

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
    setPasswordError(null)
    setConfirmPasswordError(null)
    setLoading(true)
    try {
      const detail = await confirmPasswordReset({
        token: tokenFromLink,
        new_password: password,
      })
      if (isAuthenticated) {
        await logout()
      }
      setMessage(`${detail} Zaloguj się nowym hasłem.`)
    } catch (err) {
      const apiPasswordError = getFieldError(err, 'new_password') ?? getFieldError(err, 'password')
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
      <BrandMark variant="logo" size="sm" style={styles.brand} />
      <Text style={styles.title}>{isConfirmMode ? 'Nowe hasło' : 'Reset hasła'}</Text>
      <Text style={styles.subtitle}>
        {isConfirmMode
          ? 'Ustaw nowe hasło. Link pochodzi z wiadomości e-mail.'
          : 'Wyślemy link resetujący na Twój e-mail, jeśli konto istnieje.'}
      </Text>

      <View style={styles.form}>
        {isConfirmMode ? (
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
            <Button title="Ustaw nowe hasło" loading={loading} onPress={() => void onConfirm()} />
            {message ? (
              <Button
                title="Przejdź do logowania"
                variant="secondary"
                onPress={() => router.replace('/(auth)/login')}
              />
            ) : null}
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
            <Button title="Wyślij link" loading={loading} onPress={() => void onRequest()} />
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
