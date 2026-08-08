import { Link, useFocusEffect } from 'expo-router'
import { useCallback, useEffect, useMemo, useState } from 'react'
import { RefreshControl, StyleSheet, Switch, Text, View } from 'react-native'

import { authApi } from '@/api/auth'
import { getErrorMessage } from '@/api/client'
import { patientApi } from '@/api/patient'
import type { Consent, NotificationPreference } from '@/api/types'
import { useAuth } from '@/auth/AuthContext'
import { ErrorBanner, LoadingBlock, SuccessBanner } from '@/components/AsyncState'
import { Button } from '@/components/Button'
import { Field } from '@/components/Field'
import { KeyboardAwareForm } from '@/components/KeyboardAwareForm'
import { PasswordRequirements } from '@/components/PasswordRequirements'
import { ScreenHeader, SectionCard } from '@/components/ScreenHeader'
import {
  consentLabel,
  DEFAULT_NOTIFICATION_PREFS,
  formatDate,
  isRequiredConsent,
} from '@/lib/format'
import { getPasswordError, getPasswordRequirements } from '@/lib/passwordPolicy'
import { colors, space, typography } from '@/theme/tokens'

type FeedbackKind = 'notifications' | 'consents' | 'privacy' | 'password'

export default function SettingsScreen() {
  const { logout } = useAuth()

  const [consents, setConsents] = useState<Consent[]>([])
  const [prefs, setPrefs] = useState<NotificationPreference[]>([])
  const [currentPassword, setCurrentPassword] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [pwdLoading, setPwdLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [feedback, setFeedback] = useState<{ kind: FeedbackKind; message: string } | null>(null)

  const showSuccess = useCallback((kind: FeedbackKind, message: string) => {
    setError(null)
    setFeedback({ kind, message })
  }, [])

  useEffect(() => {
    if (!feedback) {
      return
    }
    const timer = setTimeout(() => setFeedback(null), 5000)
    return () => clearTimeout(timer)
  }, [feedback])

  const load = useCallback(async () => {
    setError(null)
    try {
      const [c, n] = await Promise.all([
        patientApi.getConsents(),
        patientApi.getNotificationPreferences(),
      ])
      setConsents(c)
      setPrefs(n)
    } catch (err) {
      setError(getErrorMessage(err, 'Nie udało się pobrać ustawień.'))
    } finally {
      setLoading(false)
      setRefreshing(false)
    }
  }, [])

  useFocusEffect(
    useCallback(() => {
      setLoading(true)
      void load()
    }, [load]),
  )

  const prefMap = useMemo(() => {
    const map: Record<string, boolean> = {}
    for (const key of Object.keys(DEFAULT_NOTIFICATION_PREFS)) {
      map[key] = prefs.find((p) => p.pref_key === key)?.enabled ?? false
    }
    for (const p of prefs) {
      map[p.pref_key] = p.enabled
    }
    return map
  }, [prefs])

  async function changePassword() {
    setError(null)
    setFeedback(null)

    if (!currentPassword.trim()) {
      setError('Podaj obecne hasło.')
      return
    }
    const passwordError = getPasswordError(newPassword)
    if (passwordError) {
      setError(passwordError)
      return
    }

    setPwdLoading(true)
    try {
      const { detail } = await authApi.changePassword(currentPassword, newPassword)
      showSuccess('password', detail || 'Hasło zostało zmienione.')
      setCurrentPassword('')
      setNewPassword('')
    } catch (err) {
      setError(getErrorMessage(err, 'Nie udało się zmienić hasła.'))
    } finally {
      setPwdLoading(false)
    }
  }

  async function toggleOptionalConsent(type: 'marketing' | 'research', value: boolean) {
    setError(null)
    try {
      const next = await patientApi.updateOptionalConsents({ [type]: value })
      setConsents(next)
      showSuccess('consents', 'Zgoda została zaktualizowana.')
    } catch (err) {
      setError(getErrorMessage(err, 'Nie udało się zaktualizować zgody.'))
    }
  }

  async function togglePref(key: string, value: boolean) {
    setError(null)
    try {
      const next = await patientApi.updateNotificationPreferences({ [key]: value })
      setPrefs(next)
      showSuccess('notifications', 'Preferencje powiadomień zostały zapisane.')
    } catch (err) {
      setError(getErrorMessage(err, 'Nie udało się zapisać preferencji.'))
    }
  }

  async function exportData() {
    setError(null)
    setFeedback(null)
    try {
      await patientApi.requestDataExport()
      showSuccess('privacy', 'Wniosek o eksport danych został przyjęty.')
    } catch (err) {
      setError(getErrorMessage(err, 'Eksport nie powiódł się.'))
    }
  }

  async function requestDeletion() {
    setError(null)
    setFeedback(null)
    try {
      const { detail } = await patientApi.requestAccountDeletion()
      showSuccess('privacy', detail || 'Wniosek o usunięcie konta został zgłoszony.')
    } catch (err) {
      setError(getErrorMessage(err, 'Nie udało się zgłosić wniosku.'))
    }
  }

  if (loading) {
    return <LoadingBlock label="Ładowanie ustawień…" />
  }

  return (
    <KeyboardAwareForm
      style={styles.flex}
      contentContainerStyle={styles.content}
      bottomOffset={96}
      refreshControl={
        <RefreshControl
          refreshing={refreshing}
          onRefresh={() => {
            setRefreshing(true)
            void load()
          }}
          tintColor={colors.primary}
        />
      }
    >
      <ScreenHeader title="Ustawienia" subtitle="Powiadomienia, prywatność i konto" />

      {error ? <ErrorBanner message={error} onRetry={() => void load()} /> : null}

      <SectionCard>
        <Text style={styles.sectionTitle}>Powiadomienia</Text>
        {Object.entries(DEFAULT_NOTIFICATION_PREFS).map(([key, label]) => (
          <View key={key} style={styles.switchRow}>
            <Text style={styles.switchLabel}>{label}</Text>
            <Switch
              value={Boolean(prefMap[key])}
              onValueChange={(v) => void togglePref(key, v)}
              trackColor={{ true: colors.primary, false: colors.border }}
            />
          </View>
        ))}
        {feedback?.kind === 'notifications' ? <SuccessBanner message={feedback.message} /> : null}
      </SectionCard>

      <SectionCard>
        <Text style={styles.sectionTitle}>Zgody RODO</Text>
        {consents.map((c) => {
          const required = isRequiredConsent(c.consent_type)
          const optionalKey =
            c.consent_type === 'MARKETING_OPTIONAL'
              ? 'marketing'
              : c.consent_type === 'RESEARCH_OPTIONAL'
                ? 'research'
                : null
          return (
            <View key={c.consent_type} style={styles.switchRow}>
              <View style={{ flex: 1 }}>
                <Text style={styles.switchLabel}>{consentLabel(c.consent_type)}</Text>
                <Text style={styles.muted}>
                  {required
                    ? `Udzielono: ${formatDate(c.granted_at)}`
                    : c.granted
                      ? 'Włączone'
                      : 'Wyłączone'}
                </Text>
              </View>
              {optionalKey ? (
                <Switch
                  value={c.granted}
                  onValueChange={(v) => void toggleOptionalConsent(optionalKey, v)}
                  trackColor={{ true: colors.primary, false: colors.border }}
                />
              ) : (
                <Text style={styles.locked}>wymagana</Text>
              )}
            </View>
          )
        })}
        {!consents.some((c) => c.consent_type === 'MARKETING_OPTIONAL') ? (
          <View style={styles.switchRow}>
            <Text style={styles.switchLabel}>Marketing</Text>
            <Switch
              value={false}
              onValueChange={(v) => void toggleOptionalConsent('marketing', v)}
              trackColor={{ true: colors.primary, false: colors.border }}
            />
          </View>
        ) : null}
        {!consents.some((c) => c.consent_type === 'RESEARCH_OPTIONAL') ? (
          <View style={styles.switchRow}>
            <Text style={styles.switchLabel}>Badania naukowe</Text>
            <Switch
              value={false}
              onValueChange={(v) => void toggleOptionalConsent('research', v)}
              trackColor={{ true: colors.primary, false: colors.border }}
            />
          </View>
        ) : null}
        {feedback?.kind === 'consents' ? <SuccessBanner message={feedback.message} /> : null}
        <Button title="Eksport danych" variant="secondary" onPress={() => void exportData()} />
        <Button
          title="Wniosek o usunięcie konta"
          variant="danger"
          onPress={() => void requestDeletion()}
        />
        <Link href="/legal/privacy" style={styles.legalLink}>
          Polityka prywatności
        </Link>
        <Link href="/legal/cookies" style={styles.legalLink}>
          Polityka cookies
        </Link>
        <Link href="/legal/account-deletion" style={styles.legalLink}>
          Usuwanie konta (instrukcja)
        </Link>
        {feedback?.kind === 'privacy' ? <SuccessBanner message={feedback.message} /> : null}
      </SectionCard>

      <SectionCard>
        <Text style={styles.sectionTitle}>Zmiana hasła</Text>
        <Field
          label="Obecne hasło"
          value={currentPassword}
          onChangeText={setCurrentPassword}
          secureTextEntry
        />
        <Field
          label="Nowe hasło"
          value={newPassword}
          onChangeText={setNewPassword}
          secureTextEntry
        />
        <PasswordRequirements
          requirements={getPasswordRequirements(newPassword)}
          showErrors={newPassword.length > 0}
        />
        <Button title="Zmień hasło" loading={pwdLoading} onPress={() => void changePassword()} />
        {feedback?.kind === 'password' ? <SuccessBanner message={feedback.message} /> : null}
      </SectionCard>

      <Button
        title="Wyloguj"
        variant="ghost"
        onPress={() => {
          void logout()
        }}
      />
    </KeyboardAwareForm>
  )
}

const styles = StyleSheet.create({
  flex: { flex: 1, backgroundColor: colors.bg },
  content: { padding: space.lg, gap: space.base, paddingBottom: space['4xl'] },
  sectionTitle: { fontSize: typography.lg, fontWeight: '700', color: colors.ink },
  muted: { fontSize: typography.sm, color: colors.muted },
  switchRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    gap: space.md,
    paddingVertical: space.xs,
  },
  switchLabel: { flex: 1, color: colors.ink, fontSize: typography.base },
  locked: { color: colors.faint, fontSize: typography.xs, fontWeight: '700' },
  legalLink: { color: colors.primary, fontWeight: '600', fontSize: typography.sm },
})
