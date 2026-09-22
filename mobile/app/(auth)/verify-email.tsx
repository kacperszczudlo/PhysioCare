/**
 * @file verify-email.tsx
 * @description Ekran potwierdzania adresu e-mail za pomocą 6-cyfrowego kodu aktywacyjnego.
 */

import { Link, useLocalSearchParams, useRouter } from 'expo-router'
import { useState } from 'react'
import { StyleSheet, Text, View } from 'react-native'

import { ApiError, getErrorMessage } from '@/api/client'
import { useAuth } from '@/auth/AuthContext'
import { ErrorBanner, SuccessBanner } from '@/components/AsyncState'
import { BrandMark } from '@/components/BrandMark'
import { Button } from '@/components/Button'
import { Field } from '@/components/Field'
import { KeyboardAwareForm } from '@/components/KeyboardAwareForm'
import { colors, space, typography } from '@/theme/tokens'

function firstParam(value: string | string[] | undefined): string {
  if (Array.isArray(value)) {
    return (value[0] ?? '').trim()
  }
  return (value ?? '').trim()
}

/**
 * Ekran weryfikacji konta po rejestracji (wprowadzenie kodu OTP przesłanego na skrzynkę e-mail).
 *
 * @returns Element React Native prezentujący ekran potwierdzania adresu e-mail.
 */
export default function EmailVerifyScreen() {
  const { verifyEmail, resendEmailCode } = useAuth()
  const router = useRouter()
  const params = useLocalSearchParams<{ email?: string | string[] }>()
  const email = firstParam(params.email)

  const [code, setCode] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [message, setMessage] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  async function onVerify() {
    setError(null)
    setMessage(null)
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
      router.replace('/(tabs)')
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.message
          : getErrorMessage(err, 'Nie udało się potwierdzić e-maila.'),
      )
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
      setMessage(detail)
    } catch (err) {
      setError(getErrorMessage(err, 'Nie udało się wysłać kodu.'))
    } finally {
      setLoading(false)
    }
  }

  return (
    <KeyboardAwareForm style={styles.flex} contentContainerStyle={styles.container}>
      <BrandMark variant="logo" size="sm" style={styles.brand} />
      <Text style={styles.title}>Potwierdź e-mail</Text>
      <Text style={styles.subtitle}>
        Wysłaliśmy 6-cyfrowy kod{email ? ` na ${email}` : ''}. Wpisz go poniżej, aby aktywować
        konto.
      </Text>

      <View style={styles.form}>
        <Field
          label="Kod z e-maila"
          value={code}
          onChangeText={(value) => setCode(value.replace(/\D/g, '').slice(0, 6))}
          keyboardType="number-pad"
          autoComplete="one-time-code"
        />
        <Button title="Potwierdź" loading={loading} onPress={() => void onVerify()} />
        <Button
          title="Wyślij kod ponownie"
          variant="secondary"
          disabled={loading}
          onPress={() => void onResend()}
        />
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
