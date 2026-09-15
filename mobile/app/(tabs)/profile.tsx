import { useFocusEffect, useRouter } from 'expo-router'
import * as ImagePicker from 'expo-image-picker'
import { useCallback, useEffect, useState } from 'react'
import { Image, RefreshControl, StyleSheet, Text, View } from 'react-native'

import { getErrorMessage, getFieldError } from '@/api/client'
import { patientApi } from '@/api/patient'
import type { PatientProfile } from '@/api/types'
import { ErrorBanner, LoadingBlock } from '@/components/AsyncState'
import { MobileProfileSkeleton } from '@/components/skeletons/MobileSkeletons'
import { Button } from '@/components/Button'
import { Field } from '@/components/Field'
import { KeyboardAwareForm } from '@/components/KeyboardAwareForm'
import { PhoneField } from '@/components/PhoneField'
import { ScreenHeader, SectionCard } from '@/components/ScreenHeader'
import { useToast } from '@/components/ToastContext'
import { DEFAULT_COUNTRY_CODE } from '@/lib/countries'
import { useAuthenticatedCachedUri } from '@/lib/authMedia'
import { getPeselError } from '@/lib/peselPolicy'
import { formatPhoneForApi, getPhoneError, parseStoredPhone } from '@/lib/phonePolicy'
import { colors, space, typography } from '@/theme/tokens'

export default function ProfileScreen() {
  const router = useRouter()
  const { toast } = useToast()

  const [profile, setProfile] = useState<PatientProfile | null>(null)
  const [firstName, setFirstName] = useState('')
  const [lastName, setLastName] = useState('')
  const [phoneCountryCode, setPhoneCountryCode] = useState(DEFAULT_COUNTRY_CODE)
  const [phoneNational, setPhoneNational] = useState('')
  const [pesel, setPesel] = useState('')
  const [fieldErrors, setFieldErrors] = useState<{
    firstName?: string
    lastName?: string
    phone?: string
    pesel?: string
  }>({})
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [saving, setSaving] = useState(false)
  const [avatarLoading, setAvatarLoading] = useState(false)
  const [avatarPreviewUri, setAvatarPreviewUri] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const { uri: remoteAvatarUri } = useAuthenticatedCachedUri(
    avatarPreviewUri ? null : profile?.avatar_url,
  )
  const avatarUri = avatarPreviewUri ?? remoteAvatarUri

  const initialPhone = profile ? parseStoredPhone(profile.phone) : null
  const isDirty = Boolean(
    profile &&
    (firstName.trim() !== (profile.first_name ?? '') ||
      lastName.trim() !== (profile.last_name ?? '') ||
      phoneCountryCode !== initialPhone?.countryCode ||
      phoneNational !== initialPhone?.nationalNumber ||
      pesel !== (profile.pesel ?? '')),
  )

  const resetForm = useCallback(() => {
    if (!profile) return
    setFirstName(profile.first_name ?? '')
    setLastName(profile.last_name ?? '')
    const parsedPhone = parseStoredPhone(profile.phone)
    setPhoneCountryCode(parsedPhone.countryCode)
    setPhoneNational(parsedPhone.nationalNumber)
    setPesel(profile.pesel ?? '')
    setFieldErrors({})
  }, [profile])

  const load = useCallback(async () => {
    setError(null)
    setAvatarPreviewUri(null)
    try {
      const p = await patientApi.getProfile()
      setProfile(p)
      setFirstName(p.first_name ?? '')
      setLastName(p.last_name ?? '')
      const parsedPhone = parseStoredPhone(p.phone)
      setPhoneCountryCode(parsedPhone.countryCode)
      setPhoneNational(parsedPhone.nationalNumber)
      setPesel(p.pesel ?? '')
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

    const phoneError = getPhoneError(phoneNational, phoneCountryCode)
    const peselError = getPeselError(pesel)
    if (phoneError || peselError) {
      setFieldErrors((prev) => ({
        ...prev,
        phone: phoneError ?? undefined,
        pesel: peselError ?? undefined,
      }))
      setSaving(false)
      return
    }

    setFieldErrors({})
    try {
      const updated = await patientApi.updateProfile({
        first_name: firstName.trim() || undefined,
        last_name: lastName.trim() || undefined,
        phone: formatPhoneForApi(phoneNational, phoneCountryCode),
        pesel: pesel.trim() || null,
      })
      setProfile(updated)
      setFirstName(updated.first_name ?? '')
      setLastName(updated.last_name ?? '')
      const parsedPhone = parseStoredPhone(updated.phone)
      setPhoneCountryCode(parsedPhone.countryCode)
      setPhoneNational(parsedPhone.nationalNumber)
      setPesel(updated.pesel ?? '')
      toast.success('Dane profilu zostały zapisane.')
    } catch (err) {
      const apiFirstName = getFieldError(err, 'first_name')
      const apiLastName = getFieldError(err, 'last_name')
      const apiPhone = getFieldError(err, 'phone')
      const apiPesel = getFieldError(err, 'pesel')
      if (apiFirstName || apiLastName || apiPhone || apiPesel) {
        setFieldErrors({
          firstName: apiFirstName ?? undefined,
          lastName: apiLastName ?? undefined,
          phone: apiPhone ?? undefined,
          pesel: apiPesel ?? undefined,
        })
      }
      const errMsg = getErrorMessage(err, 'Nie udało się zapisać profilu.')
      setError(errMsg)
      toast.error(errMsg)
    } finally {
      setSaving(false)
    }
  }

  async function pickAvatar() {
    setError(null)
    const permission = await ImagePicker.requestMediaLibraryPermissionsAsync()
    if (!permission.granted) {
      const msg = 'Brak uprawnień do galerii zdjęć.'
      setError(msg)
      toast.error(msg)
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

    setAvatarPreviewUri(asset.uri)
    setAvatarLoading(true)
    try {
      const updated = await patientApi.uploadAvatar(asset.uri, mime, name)
      setProfile(updated)
      toast.success('Zdjęcie profilowe zostało zapisane.')
    } catch (err) {
      setAvatarPreviewUri(null)
      const errMsg = getErrorMessage(err, 'Nie udało się przesłać avatara.')
      setError(errMsg)
      toast.error(errMsg)
    } finally {
      setAvatarLoading(false)
    }
  }

  if (loading) {
    return <LoadingBlock label="Ładowanie profilu…" skeleton={<MobileProfileSkeleton />} />
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
          {avatarUri ? (
            <Image
              source={{ uri: avatarUri }}
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
      </SectionCard>

      <SectionCard>
        <View style={styles.sectionHeaderRow}>
          <Text style={styles.sectionTitle}>Dane kontaktowe</Text>
          {isDirty ? (
            <View style={styles.dirtyBadge}>
              <Text style={styles.dirtyBadgeText}>Niezapisane zmiany</Text>
            </View>
          ) : null}
        </View>
        <Text style={styles.muted}>{profile?.email}</Text>
        <Field
          label="Imię"
          value={firstName}
          onChangeText={(value) => {
            setFirstName(value)
            if (fieldErrors.firstName) {
              setFieldErrors((prev) => ({ ...prev, firstName: undefined }))
            }
          }}
          error={fieldErrors.firstName}
        />
        <Field
          label="Nazwisko"
          value={lastName}
          onChangeText={(value) => {
            setLastName(value)
            if (fieldErrors.lastName) {
              setFieldErrors((prev) => ({ ...prev, lastName: undefined }))
            }
          }}
          error={fieldErrors.lastName}
        />
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
        <Button
          title={isDirty ? 'Zapisz dane profilu' : 'Zapisano (brak zmian)'}
          disabled={!isDirty}
          loading={saving}
          onPress={() => void saveProfile()}
        />
        {isDirty ? (
          <Button title="Odrzuć zmiany" variant="secondary" disabled={saving} onPress={resetForm} />
        ) : null}
        {profile?.therapist ? (
          <Button
            title="Profil terapeuty"
            variant="secondary"
            onPress={() => router.push(`/therapist/${profile.therapist}`)}
          />
        ) : null}
      </SectionCard>
    </KeyboardAwareForm>
  )
}

const styles = StyleSheet.create({
  flex: { flex: 1, backgroundColor: colors.bg },
  content: { padding: space.lg, gap: space.base, paddingBottom: space['4xl'] },
  sectionHeaderRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  sectionTitle: { fontSize: typography.lg, fontWeight: '700', color: colors.ink },
  dirtyBadge: {
    backgroundColor: colors.accentSubtle,
    paddingHorizontal: space.sm,
    paddingVertical: 3,
    borderRadius: 6,
  },
  dirtyBadgeText: {
    fontSize: typography.xs,
    fontWeight: '700',
    color: colors.warning,
  },
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
})
