import { useFocusEffect, useRouter } from 'expo-router'
import * as ImagePicker from 'expo-image-picker'
import { useCallback, useEffect, useMemo, useState } from 'react'
import {
  Image,
  Linking,
  Pressable,
  RefreshControl,
  ScrollView,
  StyleSheet,
  Switch,
  Text,
  View,
} from 'react-native'

import { authApi } from '@/api/auth'
import { getErrorMessage } from '@/api/client'
import { patientApi } from '@/api/patient'
import type { Consent, MedicalDocument, NotificationPreference, PatientProfile } from '@/api/types'
import { useAuth } from '@/auth/AuthContext'
import { EmptyState, ErrorBanner, LoadingBlock, SuccessBanner } from '@/components/AsyncState'
import { Button } from '@/components/Button'
import { Field } from '@/components/Field'
import { ScreenHeader, SectionCard } from '@/components/ScreenHeader'
import {
  consentLabel,
  DEFAULT_NOTIFICATION_PREFS,
  formatDate,
  isRequiredConsent,
} from '@/lib/format'
import { resolveMediaUrl } from '@/lib/mediaUrl'
import { colors, space, typography } from '@/theme/tokens'

type FeedbackKind = 'avatar' | 'profile' | 'notifications' | 'consents' | 'privacy' | 'password'

export default function ProfileScreen() {
  const { logout } = useAuth()
  const router = useRouter()

  const [profile, setProfile] = useState<PatientProfile | null>(null)
  const [consents, setConsents] = useState<Consent[]>([])
  const [docs, setDocs] = useState<MedicalDocument[]>([])
  const [prefs, setPrefs] = useState<NotificationPreference[]>([])
  const [phone, setPhone] = useState('')
  const [pesel, setPesel] = useState('')
  const [currentPassword, setCurrentPassword] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [saving, setSaving] = useState(false)
  const [pwdLoading, setPwdLoading] = useState(false)
  const [avatarLoading, setAvatarLoading] = useState(false)
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
      const [p, c, d, n] = await Promise.all([
        patientApi.getProfile(),
        patientApi.getConsents(),
        patientApi.getDocuments(),
        patientApi.getNotificationPreferences(),
      ])
      setProfile(p)
      setPhone(p.phone ?? '')
      setPesel(p.pesel ?? '')
      setConsents(c)
      setDocs(d)
      setPrefs(n)
    } catch (err) {
      setError(getErrorMessage(err, 'Nie udało się pobrać profilu.'))
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

  async function saveProfile() {
    setSaving(true)
    setError(null)
    setFeedback(null)
    try {
      const updated = await patientApi.updateProfile({
        phone: phone.trim(),
        pesel: pesel.trim() || null,
      })
      setProfile(updated)
      showSuccess('profile', 'Dane profilu zostały zapisane.')
    } catch (err) {
      setError(getErrorMessage(err, 'Nie udało się zapisać profilu.'))
    } finally {
      setSaving(false)
    }
  }

  async function pickAvatar() {
    setError(null)
    setFeedback(null)
    const permission = await ImagePicker.requestMediaLibraryPermissionsAsync()
    if (!permission.granted) {
      setError('Brak uprawnień do galerii zdjęć.')
      return
    }

    const result = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ['images'],
      allowsEditing: true,
      aspect: [1, 1],
      quality: 0.85,
    })
    if (result.canceled || !result.assets[0]) {
      return
    }

    const asset = result.assets[0]
    const mime = asset.mimeType ?? 'image/jpeg'
    const name = asset.fileName ?? `avatar.${mime === 'image/png' ? 'png' : 'jpg'}`

    setAvatarLoading(true)
    try {
      const updated = await patientApi.uploadAvatar(asset.uri, mime, name)
      setProfile(updated)
      showSuccess('avatar', 'Zdjęcie profilowe zostało zapisane.')
    } catch (err) {
      setError(getErrorMessage(err, 'Nie udało się przesłać avatara.'))
    } finally {
      setAvatarLoading(false)
    }
  }

  async function changePassword() {
    setPwdLoading(true)
    setError(null)
    setFeedback(null)
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
    return <LoadingBlock label="Ładowanie profilu…" />
  }

  return (
    <ScrollView
      style={styles.flex}
      contentContainerStyle={styles.content}
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
      <ScreenHeader
        title="Profil"
        subtitle={profile ? `${profile.first_name} ${profile.last_name}` : undefined}
      />

      {error ? <ErrorBanner message={error} onRetry={() => void load()} /> : null}

      <SectionCard>
        <Text style={styles.sectionTitle}>Zdjęcie profilowe</Text>
        <View style={styles.avatarRow}>
          {resolveMediaUrl(profile?.avatar_url) ? (
            <Image
              source={{ uri: resolveMediaUrl(profile?.avatar_url)! }}
              style={styles.avatar}
              accessibilityIgnoresInvertColors
            />
          ) : (
            <View style={[styles.avatar, styles.avatarPlaceholder]}>
              <Text style={styles.avatarInitials}>
                {`${profile?.first_name?.[0] ?? ''}${profile?.last_name?.[0] ?? ''}`.toUpperCase() ||
                  '?'}
              </Text>
            </View>
          )}
          <View style={{ flex: 1, gap: space.sm }}>
            <Text style={styles.muted}>JPEG, PNG lub WebP · max 5 MB</Text>
            <Button
              title="Wybierz z galerii"
              variant="secondary"
              loading={avatarLoading}
              onPress={() => void pickAvatar()}
            />
          </View>
        </View>
        {feedback?.kind === 'avatar' ? <SuccessBanner message={feedback.message} /> : null}
      </SectionCard>

      <SectionCard>
        <Text style={styles.sectionTitle}>Dane kontaktowe</Text>
        <Text style={styles.muted}>{profile?.email}</Text>
        <Field label="Telefon" value={phone} onChangeText={setPhone} keyboardType="phone-pad" />
        <Field label="PESEL" value={pesel} onChangeText={setPesel} keyboardType="number-pad" />
        <Button title="Zapisz dane" loading={saving} onPress={() => void saveProfile()} />
        {feedback?.kind === 'profile' ? <SuccessBanner message={feedback.message} /> : null}
        {profile?.therapist ? (
          <Button
            title="Profil terapeuty"
            variant="secondary"
            onPress={() => router.push(`/therapist/${profile.therapist}`)}
          />
        ) : null}
      </SectionCard>

      <SectionCard>
        <Text style={styles.sectionTitle}>Dokumentacja</Text>
        {docs.length === 0 ? (
          <EmptyState title="Brak dokumentów" description="PDF-y udostępnione przez terapeutę." />
        ) : (
          docs.map((doc) => (
            <Pressable
              key={doc.id}
              onPress={() => {
                if (doc.file_url) {
                  void Linking.openURL(doc.file_url)
                }
              }}
              style={styles.docRow}
            >
              <View style={{ flex: 1 }}>
                <Text style={styles.docTitle}>{doc.title}</Text>
                <Text style={styles.muted}>{formatDate(doc.created_at)}</Text>
              </View>
              <Text style={styles.link}>Otwórz</Text>
            </Pressable>
          ))
        )}
      </SectionCard>

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
    </ScrollView>
  )
}

const styles = StyleSheet.create({
  flex: { flex: 1, backgroundColor: colors.bg },
  content: { padding: space.lg, gap: space.base, paddingBottom: space['4xl'] },
  sectionTitle: { fontSize: typography.lg, fontWeight: '700', color: colors.ink },
  muted: { fontSize: typography.sm, color: colors.muted },
  avatarRow: { flexDirection: 'row', gap: space.base, alignItems: 'center' },
  avatar: {
    width: 72,
    height: 72,
    borderRadius: 36,
    backgroundColor: colors.primarySubtle,
  },
  avatarPlaceholder: { alignItems: 'center', justifyContent: 'center' },
  avatarInitials: { fontSize: typography.xl, fontWeight: '800', color: colors.primary },
  switchRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    gap: space.md,
    paddingVertical: space.xs,
  },
  switchLabel: { flex: 1, color: colors.ink, fontSize: typography.base },
  locked: { color: colors.faint, fontSize: typography.xs, fontWeight: '700' },
  docRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: space.md,
    paddingVertical: space.sm,
  },
  docTitle: { fontWeight: '600', color: colors.ink },
  link: { color: colors.primary, fontWeight: '700' },
})
