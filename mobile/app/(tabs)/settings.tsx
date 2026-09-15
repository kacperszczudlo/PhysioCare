import { Link, useFocusEffect, useRouter } from 'expo-router'
import { useCallback, useEffect, useMemo, useState } from 'react'
import { Linking, Platform, Pressable, RefreshControl, StyleSheet, Switch, Text, View } from 'react-native'
import { Ionicons } from '@expo/vector-icons'

import { authApi } from '@/api/auth'
import { getErrorMessage } from '@/api/client'
import { patientApi } from '@/api/patient'
import type { Consent, NotificationPreference } from '@/api/types'
import { useAuth } from '@/auth/AuthContext'
import { AccountDeletionModal } from '@/components/AccountDeletionModal'
import { ErrorBanner, LoadingBlock } from '@/components/AsyncState'
import { Button } from '@/components/Button'
import { DataExportModal } from '@/components/DataExportModal'
import { Field } from '@/components/Field'
import { KeyboardAwareForm } from '@/components/KeyboardAwareForm'
import { PasswordRequirements } from '@/components/PasswordRequirements'
import { ScreenHeader, SectionCard } from '@/components/ScreenHeader'
import { useToast } from '@/components/ToastContext'
import { sharePatientDataExport } from '@/lib/dataExport'
import {
  consentLabel,
  DEFAULT_NOTIFICATION_PREFS,
  formatDate,
  isRequiredConsent,
} from '@/lib/format'
import { getPasswordError, getPasswordRequirements } from '@/lib/passwordPolicy'
import {
  getPushPermissionStatus,
  isRemotePushSupported,
  registerAndUploadPushToken,
  unregisterPushToken,
  type PushPermissionStatus,
} from '@/notifications/push'
import { colors, radius, space, typography } from '@/theme/tokens'

export default function SettingsScreen() {
  const { logout, user } = useAuth()
  const router = useRouter()
  const { toast } = useToast()

  const [consents, setConsents] = useState<Consent[]>([])
  const [prefs, setPrefs] = useState<NotificationPreference[]>([])
  const [currentPassword, setCurrentPassword] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [pwdLoading, setPwdLoading] = useState(false)
  const [pushPermission, setPushPermission] = useState<PushPermissionStatus>('undetermined')
  const [pushBusy, setPushBusy] = useState(false)
  const [deletionOpen, setDeletionOpen] = useState(false)
  const [deletionBusy, setDeletionBusy] = useState(false)
  const [exportOpen, setExportOpen] = useState(false)
  const [exportBusy, setExportBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const load = useCallback(async () => {
    setError(null)
    try {
      const [c, n] = await Promise.all([
        patientApi.getConsents(),
        patientApi.getNotificationPreferences(),
      ])
      setConsents(c)
      setPrefs(n)
      setPushPermission(await getPushPermissionStatus())
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
      map[key] = prefs.find((p) => p.pref_key === key)?.enabled ?? true
    }
    for (const p of prefs) {
      map[p.pref_key] = p.enabled
    }
    return map
  }, [prefs])

  async function changePassword() {
    setError(null)

    if (!currentPassword.trim()) {
      const msg = 'Podaj obecne hasło.'
      setError(msg)
      toast.error(msg)
      return
    }
    const passwordError = getPasswordError(newPassword)
    if (passwordError) {
      setError(passwordError)
      toast.error(passwordError)
      return
    }

    setPwdLoading(true)
    try {
      await authApi.changePassword(currentPassword, newPassword)
      toast.success('Hasło zostało zmienione.')
      setCurrentPassword('')
      setNewPassword('')
      await logout()
    } catch (err) {
      const errMsg = getErrorMessage(err, 'Nie udało się zmienić hasła.')
      setError(errMsg)
      toast.error(errMsg)
    } finally {
      setPwdLoading(false)
    }
  }

  async function toggleOptionalConsent(type: 'marketing' | 'research', value: boolean) {
    setError(null)
    try {
      const next = await patientApi.updateOptionalConsents({ [type]: value })
      setConsents(next)
      toast.success('Zgoda została zaktualizowana.')
    } catch (err) {
      const errMsg = getErrorMessage(err, 'Nie udało się zaktualizować zgody.')
      setError(errMsg)
      toast.error(errMsg)
    }
  }

  async function togglePref(key: string, value: boolean) {
    setError(null)
    try {
      const next = await patientApi.updateNotificationPreferences({ [key]: value })
      setPrefs(next)
      toast.success('Preferencje powiadomień zostały zapisane.')
    } catch (err) {
      const errMsg = getErrorMessage(err, 'Nie udało się zapisać preferencji.')
      setError(errMsg)
      toast.error(errMsg)
    }
  }

  async function enableSystemNotifications() {
    setError(null)
    setPushBusy(true)
    try {
      if (pushPermission === 'denied') {
        await Linking.openSettings()
        return
      }
      const token = await registerAndUploadPushToken()
      const status = await getPushPermissionStatus()
      setPushPermission(status)
      if (token) {
        toast.success('Powiadomienia systemowe zostały włączone.')
        return
      }
      if (status !== 'granted') {
        const msg = 'Aby dostawać powiadomienia na telefon, włącz je w ustawieniach systemu.'
        setError(msg)
        toast.error(msg)
        return
      }
      const msg = 'Push działa na fizycznym telefonie w Expo Go lub w buildzie EAS.'
      setError(msg)
      toast.warning(msg)
    } catch (err) {
      const errMsg = getErrorMessage(err, 'Nie udało się włączyć powiadomień systemowych.')
      setError(errMsg)
      toast.error(errMsg)
    } finally {
      setPushBusy(false)
    }
  }

  async function runDataExport() {
    setError(null)
    setExportBusy(true)
    try {
      const payload = await patientApi.requestDataExport()
      const result = await sharePatientDataExport(payload)
      setExportOpen(false)
      if (result.delivered && result.mode === 'saved') {
        toast.success(
          `Zapisano plik ${result.fileName}. Znajdziesz go w wybranym folderze (np. Pobrane).`,
        )
      } else if (result.delivered) {
        toast.success(
          `Plik ${result.fileName} jest gotowy — możesz go zapisać lub wysłać sobie.`,
        )
      } else {
        toast.info(
          `Plik ${result.fileName} został przygotowany. Spróbuj ponownie, jeśli nie zapisałeś go jeszcze.`,
        )
      }
    } catch (err) {
      const errMsg = getErrorMessage(err, 'Eksport nie powiódł się.')
      setError(errMsg)
      toast.error(errMsg)
    } finally {
      setExportBusy(false)
    }
  }

  async function requestDeletion(reason: string) {
    setError(null)
    setDeletionBusy(true)
    try {
      // Unregister push while the session is still valid (deletion deactivates the user).
      await unregisterPushToken()
      await patientApi.requestAccountDeletion(reason)
      setDeletionOpen(false)
      toast.success('Wniosek o usunięcie konta został złożony.')
      await logout()
    } catch (err) {
      const errMsg = getErrorMessage(err, 'Nie udało się zgłosić wniosku.')
      setError(errMsg)
      toast.error(errMsg)
    } finally {
      setDeletionBusy(false)
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
        {pushPermission === 'granted' ? (
          <Text style={styles.muted}>Powiadomienia systemowe są włączone na tym urządzeniu.</Text>
        ) : !isRemotePushSupported() || pushPermission === 'unsupported' ? (
          <Text style={styles.muted}>
            {Platform.OS === 'web'
              ? 'Push działa w aplikacji na telefonie. Tutaj przypomnienia mogą iść na e-mail.'
              : 'Expo Go od SDK 53 nie obsługuje zdalnego pusha (szczególnie Android). Zgoda systemowa nic tu nie zmienia - przypomnienia idą na e-mail. Żeby dostać push, zbuduj aplikację: npx expo run:android.'}
          </Text>
        ) : (
          <>
            <Text style={styles.muted}>
              Bez zgody systemowej przypomnienia przyjdą na e-mail (o ile dany typ jest włączony
              poniżej).
            </Text>
            <Button
              title={
                pushPermission === 'denied'
                  ? 'Otwórz ustawienia systemu'
                  : 'Włącz powiadomienia systemowe'
              }
              variant="secondary"
              loading={pushBusy}
              onPress={() => void enableSystemNotifications()}
            />
          </>
        )}
        {Object.entries(DEFAULT_NOTIFICATION_PREFS).map(([key, label]) => (
          <View key={key} style={styles.switchRow}>
            <Text style={styles.switchLabel}>{label}</Text>
            <Switch
              value={Boolean(prefMap[key])}
              onValueChange={(v) => void togglePref(key, v)}
              trackColor={{ true: colors.primary, false: colors.borderStrong }}
              thumbColor={colors.surface}
              ios_backgroundColor={colors.borderStrong}
            />
          </View>
        ))}
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
                  trackColor={{ true: colors.primary, false: colors.borderStrong }}
                  thumbColor={colors.surface}
                  ios_backgroundColor={colors.borderStrong}
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
              trackColor={{ true: colors.primary, false: colors.borderStrong }}
              thumbColor={colors.surface}
              ios_backgroundColor={colors.borderStrong}
            />
          </View>
        ) : null}
        {!consents.some((c) => c.consent_type === 'RESEARCH_OPTIONAL') ? (
          <View style={styles.switchRow}>
            <Text style={styles.switchLabel}>Badania naukowe</Text>
            <Switch
              value={false}
              onValueChange={(v) => void toggleOptionalConsent('research', v)}
              trackColor={{ true: colors.primary, false: colors.borderStrong }}
              thumbColor={colors.surface}
              ios_backgroundColor={colors.borderStrong}
            />
          </View>
        ) : null}
        <Button
          title="Eksport danych"
          variant="secondary"
          loading={exportBusy}
          onPress={() => setExportOpen(true)}
        />
        <Button
          title="Wniosek o usunięcie konta"
          variant="danger"
          onPress={() => setDeletionOpen(true)}
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
      </SectionCard>

      <DataExportModal
        open={exportOpen}
        busy={exportBusy}
        onClose={() => {
          if (!exportBusy) {
            setExportOpen(false)
          }
        }}
        onConfirm={() => void runDataExport()}
      />

      <AccountDeletionModal
        open={deletionOpen}
        busy={deletionBusy}
        onClose={() => {
          if (!deletionBusy) {
            setDeletionOpen(false)
          }
        }}
        onConfirm={requestDeletion}
      />

      <SectionCard>
        <Text style={styles.sectionTitle}>Zmiana hasła</Text>
        <Text style={styles.sectionHint}>
          Znasz obecne hasło? Zmień je poniżej. Nie pamiętasz - wyślemy 6-cyfrowy kod na e-mail (tak
          jak przy logowaniu).
        </Text>
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
        <Button
          title="Nie pamiętam hasła"
          variant="secondary"
          onPress={() => {
            const email = user?.email?.trim()
            router.push(
              email ? { pathname: '/password-reset', params: { email } } : '/password-reset',
            )
          }}
        />
      </SectionCard>

      <SectionCard accessibilityLabel="Sesja">
        <Text style={styles.sectionTitle}>Sesja</Text>
        <Text style={styles.sectionHint}>Aktywne połączenie z aplikacją.</Text>
        <Button
          title="Wyloguj się"
          variant="danger"
          onPress={() => {
            void logout()
          }}
        />
      </SectionCard>
    </KeyboardAwareForm>
  )
}

const styles = StyleSheet.create({
  flex: { flex: 1, backgroundColor: colors.bg },
  content: { padding: space.lg, gap: space.base, paddingBottom: space['4xl'] },
  sectionTitle: { fontSize: typography.lg, fontWeight: '700', color: colors.ink },
  sectionHint: { fontSize: typography.sm, color: colors.muted, marginBottom: space.xs },
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
