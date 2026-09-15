import { Link, useLocalSearchParams, useRouter, type Href } from 'expo-router'
import { useState } from 'react'
import { StyleSheet, Text, View } from 'react-native'

import { ApiError, getErrorMessage } from '@/api/client'
import { useAuth } from '@/auth/AuthContext'
import { setGoogleRegistrationDraft } from '@/auth/googleRegistrationDraft'
import { GoogleSignInButton, isGoogleSignInConfigured } from '@/auth/googleSignIn'
import { parseGoogleIdTokenClaims } from '@/auth/parseGoogleIdToken'
import { SuccessBanner } from '@/components/AsyncState'
import { BrandMark } from '@/components/BrandMark'
import { Button } from '@/components/Button'
import { Field } from '@/components/Field'
import { KeyboardAwareForm } from '@/components/KeyboardAwareForm'
import { useToast } from '@/components/ToastContext'
import { colors, space, typography } from '@/theme/tokens'

function firstParam(value: string | string[] | undefined): string {
  if (Array.isArray(value)) {
    return (value[0] ?? '').trim()
  }
  return (value ?? '').trim()
}

export default function LoginScreen() {
  const { login, loginWithGoogle } = useAuth()
  const router = useRouter()
  const { toast } = useToast()
  const params = useLocalSearchParams<{ email?: string | string[]; reset?: string | string[] }>()
  const emailFromParams = firstParam(params.email)
  const resetNotice = firstParam(params.reset) === '1'

  const [email, setEmail] = useState(emailFromParams)
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  async function onSubmit() {
    setError(null)
    const trimmedEmail = email.trim()
    if (!trimmedEmail) {
      setError('Podaj adres e-mail.')
      return
    }
    if (!password) {
      setError('Podaj hasło.')
      return
    }
    setLoading(true)
    try {
      await login(trimmedEmail, password)
      router.replace('/(tabs)')
    } catch (err) {
      if (err instanceof ApiError && err.code === 'AUTH_027') {
        const details = err.details as { email?: string }
        const verifyEmailAddr = (typeof details.email === 'string' && details.email) || trimmedEmail
        router.replace(`/(auth)/verify-email?email=${encodeURIComponent(verifyEmailAddr)}` as Href)
        return
      }
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
    } catch (err: unknown) {
      const anyErr = err as Record<string, any> | null | undefined
      const isNotFound =
        anyErr &&
        (anyErr.code === 'AUTH_025' ||
          anyErr.status === 404 ||
          Boolean(anyErr.details?.needs_registration) ||
          Boolean(anyErr.body?.error?.details?.needs_registration) ||
          (typeof anyErr.message === 'string' &&
            /brak konta|nie znaleziono|dokończ rejestrację/i.test(anyErr.message)))

      if (isNotFound) {
        const details = (anyErr?.details || anyErr?.body?.error?.details || {}) as {
          email?: string
          first_name?: string
          last_name?: string
        }
        const claims = parseGoogleIdTokenClaims(idToken)
        setGoogleRegistrationDraft({
          credential: idToken,
          email: (typeof details.email === 'string' && details.email) || claims.email || undefined,
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

  function handleGoogleError(message: string) {
    if (/anulowane/i.test(message)) {
      toast.info(message)
    } else {
      toast.error(message)
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
        {resetNotice ? (
          <SuccessBanner message="Hasło zostało zmienione. Zaloguj się nowym hasłem." />
        ) : null}
        {error ? (
          <Text style={styles.error} accessibilityRole="alert">
            {error}
          </Text>
        ) : null}
        <Button
          title="Zaloguj się"
          loading={loading}
          disabled={!email.trim() || !password}
          onPress={onSubmit}
        />

        {isGoogleSignInConfigured ? (
          <GoogleSignInButton
            loading={loading}
            title="Kontynuuj z Google"
            hint="Nowe konto? Google przeniesie Cię do dokończenia rejestracji (zgody RODO)."
            onSuccess={onGoogleSuccess}
            onError={handleGoogleError}
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
  dot: { color: colors.muted },
})
