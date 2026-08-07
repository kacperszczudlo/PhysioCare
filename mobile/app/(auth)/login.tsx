import { Link, useRouter } from 'expo-router'
import { useState } from 'react'
import { StyleSheet, Text, View } from 'react-native'

import { getErrorMessage } from '@/api/client'
import { useAuth } from '@/auth/AuthContext'
import { Button } from '@/components/Button'
import { Field } from '@/components/Field'
import { KeyboardAwareForm } from '@/components/KeyboardAwareForm'
import { colors, space, typography } from '@/theme/tokens'

export default function LoginScreen() {
  const { login } = useAuth()
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

  return (
    <KeyboardAwareForm style={styles.flex} contentContainerStyle={styles.container}>
      <View style={styles.brand}>
        <Text style={styles.brandName}>PhysioCare</Text>
        <Text style={styles.brandTag}>Twoja terapia w kieszeni</Text>
      </View>

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
      </View>

      <View style={styles.footer}>
        <Link href="/(auth)/register" style={styles.link}>
          Załóż konto
        </Link>
        <Text style={styles.dot}>·</Text>
        <Link href="/(auth)/password-reset" style={styles.link}>
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
  brand: { gap: space.xs, marginBottom: space.base },
  brandName: {
    fontSize: typography['3xl'],
    fontWeight: '800',
    color: colors.primary,
    letterSpacing: -0.5,
  },
  brandTag: { fontSize: typography.base, color: colors.muted },
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
  link: { color: colors.primary, fontWeight: '600', fontSize: typography.sm },
  dot: { color: colors.faint },
})
