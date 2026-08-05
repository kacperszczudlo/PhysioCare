import { Link, useRouter } from 'expo-router'
import { useMemo, useState } from 'react'
import {
  KeyboardAvoidingView,
  Platform,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from 'react-native'

import { getErrorMessage } from '@/api/client'
import { useAuth } from '@/auth/AuthContext'
import { Button } from '@/components/Button'
import { Field } from '@/components/Field'
import { colors, radius, space, typography } from '@/theme/tokens'

export default function RegisterScreen() {
  const { register } = useAuth()
  const router = useRouter()

  const [firstName, setFirstName] = useState('')
  const [lastName, setLastName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [therapistId, setTherapistId] = useState('')
  const [terms, setTerms] = useState(false)
  const [medical, setMedical] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  const canSubmit = useMemo(
    () =>
      terms &&
      medical &&
      firstName.trim() &&
      lastName.trim() &&
      email.trim() &&
      password.length >= 8 &&
      therapistId.trim(),
    [terms, medical, firstName, lastName, email, password, therapistId],
  )

  async function onSubmit() {
    if (!canSubmit) {
      setError('Uzupełnij formularz i zaznacz wymagane zgody RODO.')
      return
    }
    setError(null)
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
      setError(getErrorMessage(err, 'Rejestracja nie powiodła się.'))
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
        <Text style={styles.brand}>PhysioCare</Text>
        <Text style={styles.title}>Rejestracja pacjenta</Text>
        <Text style={styles.subtitle}>
          Załóż konto i zaakceptuj wymagane zgody, aby korzystać z zaleceń terapeuty.
        </Text>

        <View style={styles.form}>
          <Field
            label="Imię"
            value={firstName}
            onChangeText={setFirstName}
            autoComplete="given-name"
          />
          <Field
            label="Nazwisko"
            value={lastName}
            onChangeText={setLastName}
            autoComplete="family-name"
          />
          <Field
            label="E-mail"
            value={email}
            onChangeText={setEmail}
            autoCapitalize="none"
            keyboardType="email-address"
            autoComplete="email"
          />
          <Field
            label="Hasło"
            value={password}
            onChangeText={setPassword}
            secureTextEntry
            autoComplete="new-password"
            hint="Minimum 8 znaków"
          />
          <Field
            label="Kod terapeuty"
            value={therapistId}
            onChangeText={setTherapistId}
            autoCapitalize="none"
            autoCorrect={false}
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

          <Button title="Utwórz konto" loading={loading} disabled={!canSubmit} onPress={onSubmit} />
        </View>

        <Link href="/(auth)/login" style={styles.link}>
          Mam już konto — zaloguj się
        </Link>
      </ScrollView>
    </KeyboardAvoidingView>
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
