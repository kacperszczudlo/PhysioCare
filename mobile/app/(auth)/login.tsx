import { Link, useRouter } from 'expo-router'
import { useState } from 'react'
import { StyleSheet, Text, View } from 'react-native'

import { ApiError, getErrorMessage } from '@/api/client'
import { useAuth } from '@/auth/AuthContext'
import { setGoogleRegistrationDraft } from '@/auth/googleRegistrationDraft'
import { GoogleSignInButton, isGoogleSignInConfigured } from '@/auth/googleSignIn'
import { parseGoogleIdTokenClaims } from '@/auth/parseGoogleIdToken'
import { BrandMark } from '@/components/BrandMark'
import { Button } from '@/components/Button'
import { Field } from '@/components/Field'
import { KeyboardAwareForm } from '@/components/KeyboardAwareForm'
import { colors, space, typography } from '@/theme/tokens'

export default function LoginScreen() {
  const { login, loginWithGoogle } = useAuth()
  const router = useRouter()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  async function onSubmit() {
    setError(null)
    setLoading(true)
    try {
      await login(email.trim(), password)
      router.replace('/(tabs)')
    } catch (err) {
      setError(getErrorMessage(err, 'Nie udało się zalogować.'))
    } finally {
      setLoading(false)
    }
  }

  async function onGoogleSuccess(idToken: string) {
    setError(null)
    setLoading(true)
    try {
      await loginWithGoogle(idToken)
      router.replace('/(tabs)')
    } catch (err) {
      if (err instanceof ApiError && err.code === 'AUTH_025') {
        const details = err.details as {
          email?: string
          first_name?: string
          last_name?: string
        }
        const claims = parseGoogleIdTokenClaims(idToken)
        setGoogleRegistrationDraft({
          credential: idToken,
          email:
            (typeof details.email === 'string' && details.email) || claims.email || undefined,
          first_name:
            (typeof details.first_name === 'string' && details.first_name) ||
            claims.first_name ||
            undefined,
          last_name:
            (typeof details.last_name === 'string' && details.last_name) ||
            claims.last_name ||
            undefined,
        })
        router.replace('/(auth)/register')
        return
      }
      setError(getErrorMessage(err, 'Nie udało się zalogować przez Google.'))
    } finally {
      setLoading(false)
    }
  }

  return (
    <KeyboardAwareForm style={styles.flex} contentContainerStyle={styles.container}>
      <BrandMark variant="logo" size="lg" style={styles.brand} />

      <Text style={styles.title}>Logowanie</Text>
      <Text style={styles.subtitle}>Wejdź do konta pacjenta.</Text>

      <View style={styles.form}>
        <Field
          label="E-mail"
          autoCapitalize="none"
          autoComplete="email"
          keyboardType="email-address"
          value={email}
          onChangeText={setEmail}
        />
        <Field
          label="Hasło"
          secureTextEntry
          autoComplete="password"
          value={password}
          onChangeText={setPassword}
        />
        {error ? (
          <Text style={styles.error} accessibilityRole="alert">
            {error}
          </Text>
        ) : null}
        <Button title="Zaloguj się" loading={loading} onPress={onSubmit} />

        {isGoogleSignInConfigured ? (
          <GoogleSignInButton
            loading={loading}
            title="Kontynuuj z Google"
            hint="Nowe konto? Google przeniesie Cię do rejestracji (kod terapeuty + zgody)."
            onSuccess={onGoogleSuccess}
            onError={setError}
          />
        ) : null}
      </View>

      <View style={styles.footer}>
        <Link href="/(auth)/register" style={styles.link}>
          Załóż konto
        </Link>
        <Text style={styles.dot}>·</Text>
        <Link href="/password-reset" style={styles.link}>
          Nie pamiętam hasła
        </Link>
      </View>
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
    gap: space.base,
  },
  brand: { marginBottom: space.base, alignSelf: 'center', alignItems: 'center' },
  title: { fontSize: typography['2xl'], fontWeight: '700', color: colors.ink },
  subtitle: { fontSize: typography.sm, color: colors.muted, marginBottom: space.sm },
  form: { gap: space.base },
  error: { color: colors.danger, fontSize: typography.sm },
  footer: {
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    gap: space.sm,
    marginTop: space.base,
  },
  link: {
    color: colors.primary,
    fontWeight: '600',
    fontSize: typography.sm,
    textDecorationLine: 'underline',
  },
  dot: { color: colors.faint },
})
