import { useFocusEffect, useRouter } from 'expo-router'
import * as ImagePicker from 'expo-image-picker'
import { useCallback, useEffect, useState } from 'react'
import {
  Image,
  Linking,
  Pressable,
  RefreshControl,
  StyleSheet,
  Text,
  View,
} from 'react-native'

import { getErrorMessage, getFieldError } from '@/api/client'
import { patientApi } from '@/api/patient'
import type { MedicalDocument, PatientProfile } from '@/api/types'
import { EmptyState, ErrorBanner, LoadingBlock, SuccessBanner } from '@/components/AsyncState'
import { Button } from '@/components/Button'
import { Field } from '@/components/Field'
import { KeyboardAwareForm } from '@/components/KeyboardAwareForm'
import { PhoneField } from '@/components/PhoneField'
import { ScreenHeader, SectionCard } from '@/components/ScreenHeader'
import { DEFAULT_COUNTRY_CODE } from '@/lib/countries'
import { formatDate } from '@/lib/format'
import { resolveMediaUrl } from '@/lib/mediaUrl'
import { getPeselError } from '@/lib/peselPolicy'
import { formatPhoneForApi, getPhoneError, parseStoredPhone } from '@/lib/phonePolicy'
import { colors, space, typography } from '@/theme/tokens'

type FeedbackKind = 'avatar' | 'profile'

export default function ProfileScreen() {
  const router = useRouter()

  const [profile, setProfile] = useState<PatientProfile | null>(null)
  const [docs, setDocs] = useState<MedicalDocument[]>([])
  const [phoneCountryCode, setPhoneCountryCode] = useState(DEFAULT_COUNTRY_CODE)
  const [phoneNational, setPhoneNational] = useState('')
  const [pesel, setPesel] = useState('')
  const [fieldErrors, setFieldErrors] = useState<{ phone?: string; pesel?: string }>({})
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [saving, setSaving] = useState(false)
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
      const [p, d] = await Promise.all([patientApi.getProfile(), patientApi.getDocuments()])
      setProfile(p)
      const parsedPhone = parseStoredPhone(p.phone)
      setPhoneCountryCode(parsedPhone.countryCode)
      setPhoneNational(parsedPhone.nationalNumber)
      setPesel(p.pesel ?? '')
      setDocs(d)
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

  async function saveProfile() {
    setSaving(true)
    setError(null)
    setFeedback(null)

    const phoneError = getPhoneError(phoneNational, phoneCountryCode)
    const peselError = getPeselError(pesel)
    if (phoneError || peselError) {
      setFieldErrors({
        phone: phoneError ?? undefined,
        pesel: peselError ?? undefined,
      })
      setSaving(false)
      return
    }

    setFieldErrors({})
    try {
      const updated = await patientApi.updateProfile({
        phone: formatPhoneForApi(phoneNational, phoneCountryCode),
        pesel: pesel.trim() || null,
      })
      setProfile(updated)
      const parsedPhone = parseStoredPhone(updated.phone)
      setPhoneCountryCode(parsedPhone.countryCode)
      setPhoneNational(parsedPhone.nationalNumber)
      setPesel(updated.pesel ?? '')
      showSuccess('profile', 'Dane profilu zostały zapisane.')
    } catch (err) {
      const apiPhone = getFieldError(err, 'phone')
      const apiPesel = getFieldError(err, 'pesel')
      if (apiPhone || apiPesel) {
        setFieldErrors({
          phone: apiPhone ?? undefined,
          pesel: apiPesel ?? undefined,
        })
      }
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

  if (loading) {
    return <LoadingBlock label="Ładowanie profilu…" />
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
        <PhoneField
          countryCode={phoneCountryCode}
          nationalNumber={phoneNational}
          onCountryChange={(code) => {
            setPhoneCountryCode(code)
            if (fieldErrors.phone) {
              setFieldErrors((prev) => ({ ...prev, phone: undefined }))
            }
          }}
          onNationalNumberChange={(value) => {
            setPhoneNational(value)
            if (fieldErrors.phone) {
              setFieldErrors((prev) => ({ ...prev, phone: undefined }))
            }
          }}
          error={fieldErrors.phone}
          hint="Wybierz kraj, żeby ustawić prefix numeru."
        />
        <Field
          label="PESEL"
          value={pesel}
          onChangeText={(value) => {
            setPesel(value)
            if (fieldErrors.pesel) {
              setFieldErrors((prev) => ({ ...prev, pesel: undefined }))
            }
          }}
          keyboardType="number-pad"
          maxLength={11}
          error={fieldErrors.pesel}
          hint="11 cyfr z poprawną sumą kontrolną"
        />
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
    </KeyboardAwareForm>
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
  docRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: space.md,
    paddingVertical: space.sm,
  },
  docTitle: { fontWeight: '600', color: colors.ink },
  link: { color: colors.primary, fontWeight: '700' },
})
