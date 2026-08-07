import { Link } from 'expo-router'
import { useState } from 'react'
import { KeyboardAvoidingView, Platform, ScrollView, StyleSheet, Text, View } from 'react-native'

import { getErrorMessage } from '@/api/client'
import { useAuth } from '@/auth/AuthContext'
import { Button } from '@/components/Button'
import { Field } from '@/components/Field'
import { colors, space, typography } from '@/theme/tokens'

export default function PasswordResetScreen() {
  const { requestPasswordReset, confirmPasswordReset } = useAuth()
  const [step, setStep] = useState<'request' | 'confirm'>('request')
  const [email, setEmail] = useState('')
  const [token, setToken] = useState('')
  const [password, setPassword] = useState('')
  const [message, setMessage] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  async function onRequest() {
    setError(null)
    setMessage(null)
    setLoading(true)
    try {
      const detail = await requestPasswordReset(email.trim())
      setMessage(detail)
      setStep('confirm')
    } catch (err) {
      setError(getErrorMessage(err, 'Nie udało się wysłać linku.'))
    } finally {
      setLoading(false)
    }
  }

  async function onConfirm() {
    setError(null)
    setMessage(null)
    setLoading(true)
    try {
      const detail = await confirmPasswordReset({
        token: token.trim(),
        new_password: password,
      })
      setMessage(detail)
    } catch (err) {
      setError(getErrorMessage(err, 'Nie udało się ustawić hasła.'))
    } finally {
      setLoading(false)
    }
  }

  return (
    <KeyboardAvoidingView
      style={styles.flex}
      behavior={Platform.OS === 'ios' ? 'padding' : undefined}
    >
      <ScrollView contentContainerStyle={styles.container} keyboardShouldPersistTaps="handled">
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
                onChangeText={setEmail}
                autoCapitalize="none"
                keyboardType="email-address"
              />
              <Button title="Wyślij token" loading={loading} onPress={onRequest} />
            </>
          ) : (
            <>
              <Field label="Token" value={token} onChangeText={setToken} autoCapitalize="none" />
              <Field
                label="Nowe hasło"
                value={password}
                onChangeText={setPassword}
                secureTextEntry
              />
              <Button title="Ustaw nowe hasło" loading={loading} onPress={onConfirm} />
              <Button title="Wróć do e-maila" variant="ghost" onPress={() => setStep('request')} />
            </>
          )}

          {message ? <Text style={styles.ok}>{message}</Text> : null}
          {error ? (
            <Text style={styles.error} accessibilityRole="alert">
              {error}
            </Text>
          ) : null}
        </View>

        <Link href="/(auth)/login" style={styles.link}>
          Powrót do logowania
        </Link>
      </ScrollView>
    </KeyboardAvoidingView>
  )
}

const styles = StyleSheet.create({
  flex: { flex: 1, backgroundColor: colors.bg },
  container: { flexGrow: 1, padding: space.xl, justifyContent: 'center', gap: space.md },
  title: { fontSize: typography['2xl'], fontWeight: '700', color: colors.ink },
  subtitle: { fontSize: typography.sm, color: colors.muted, marginBottom: space.sm },
  form: { gap: space.base },
  ok: { color: colors.success, fontSize: typography.sm },
  error: { color: colors.danger, fontSize: typography.sm },
  link: {
    color: colors.primary,
    fontWeight: '600',
    textAlign: 'center',
    marginTop: space.base,
  },
})
