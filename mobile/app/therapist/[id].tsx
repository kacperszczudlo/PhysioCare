import { Stack, useLocalSearchParams } from 'expo-router'
import { useCallback, useEffect, useMemo, useState } from 'react'
import { Image, Linking, Pressable, ScrollView, StyleSheet, Text, View } from 'react-native'

import { getErrorMessage } from '@/api/client'
import { patientApi } from '@/api/patient'
import type { TherapistPublic } from '@/api/types'
import { ErrorBanner, LoadingBlock } from '@/components/AsyncState'
import { Button } from '@/components/Button'
import { SectionCard } from '@/components/ScreenHeader'
import { LocationMapCard } from '@/components/LocationMapCard'
import { useAuthenticatedCachedUri } from '@/lib/authMedia'
import { colors, radius, space, typography } from '@/theme/tokens'

function yearsLabel(years: number): string {
  if (years === 1) {
    return '1 rok stażu'
  }
  if (years >= 2 && years <= 4) {
    return `${years} lata stażu`
  }
  return `${years} lat stażu`
}

export default function TherapistPublicScreen() {
  const { id } = useLocalSearchParams<{ id: string }>()
  const [therapist, setTherapist] = useState<TherapistPublic | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [avatarFailed, setAvatarFailed] = useState(false)
  const [expandedCode, setExpandedCode] = useState<string | null>(null)
  const { uri: avatarUri, error: avatarLoadError } = useAuthenticatedCachedUri(
    therapist?.avatar_url,
  )

  const load = useCallback(async () => {
    if (!id) {
      return
    }
    setError(null)
    setLoading(true)
    try {
      setTherapist(await patientApi.getTherapistPublic(id))
      setAvatarFailed(false)
    } catch (err) {
      setError(getErrorMessage(err, 'Nie udało się pobrać profilu terapeuty.'))
    } finally {
      setLoading(false)
    }
  }, [id])

  useEffect(() => {
    void load()
  }, [load])

  const allowed = useMemo(
    () => therapist?.competences?.capabilities.filter((cap) => cap.allowed) ?? [],
    [therapist],
  )

  if (loading) {
    return <LoadingBlock />
  }

  if (!therapist) {
    return (
      <View style={styles.pad}>
        <ErrorBanner message={error ?? 'Nie znaleziono terapeuty.'} onRetry={() => void load()} />
      </View>
    )
  }

  const fullName = `${therapist.first_name} ${therapist.last_name}`
  const initials =
    `${therapist.first_name?.[0] ?? ''}${therapist.last_name?.[0] ?? ''}`.toUpperCase()
  const showAvatar = Boolean(avatarUri) && !avatarFailed && !avatarLoadError
  const qualification =
    therapist.qualification_label ?? therapist.competences?.qualification_label ?? null
  const experienceYears =
    therapist.experience_years ?? therapist.competences?.experience_years ?? null

  return (
    <>
      <Stack.Screen options={{ title: fullName }} />
      <ScrollView style={styles.flex} contentContainerStyle={styles.content}>
        {error ? <ErrorBanner message={error} onRetry={() => void load()} /> : null}

        <SectionCard>
          <View style={styles.hero}>
            {showAvatar ? (
              <View style={styles.avatarClip}>
                <Image
                  source={{ uri: avatarUri! }}
                  style={styles.avatar}
                  resizeMode="cover"
                  onError={() => setAvatarFailed(true)}
                  accessibilityIgnoresInvertColors
                />
              </View>
            ) : (
              <View style={[styles.avatar, styles.avatarPlaceholder]}>
                <Text style={styles.initials}>{initials || '?'}</Text>
              </View>
            )}
            <View style={styles.heroText}>
              <Text style={styles.name}>{fullName}</Text>
              {qualification ? <Text style={styles.qualification}>{qualification}</Text> : null}
              {experienceYears != null ? (
                <Text style={styles.muted}>{yearsLabel(experienceYears)}</Text>
              ) : null}
              <Text style={styles.bio}>{therapist.bio || 'Brak biogramu.'}</Text>
            </View>
          </View>
        </SectionCard>

        {therapist.competences ? (
          <SectionCard>
            <Text style={styles.section}>Uprawnienia</Text>
            <Text style={styles.muted}>
              {qualification ?? 'Fizjoterapeuta'}
              {experienceYears != null ? ` · ${yearsLabel(experienceYears)}` : ''}
            </Text>

            {therapist.competences.can_plan_therapy ||
            therapist.competences.can_supervise ||
            therapist.competences.is_fizjo_spec ||
            therapist.competences.device_groups.length > 0 ? (
              <View style={styles.chipRow}>
                {therapist.competences.can_plan_therapy ? (
                  <Text style={[styles.chip, styles.chipOk]}>Planowanie terapii</Text>
                ) : null}
                {therapist.competences.can_supervise ? (
                  <Text style={[styles.chip, styles.chipOk]}>Nadzór</Text>
                ) : null}
                {therapist.competences.is_fizjo_spec ? (
                  <Text style={[styles.chip, styles.chipOk]}>FIZJO SPEC</Text>
                ) : null}
                {therapist.competences.device_groups.length > 0 ? (
                  <Text style={[styles.chip, styles.chipOk]}>
                    Wyroby: {therapist.competences.device_groups.join(', ')}
                  </Text>
                ) : null}
              </View>
            ) : null}

            {allowed.length === 0 ? (
              <Text style={styles.muted}>Brak dodatkowych uprawnień w profilu.</Text>
            ) : (
              allowed.map((cap) => {
                const open = expandedCode === cap.code
                return (
                  <Pressable
                    key={cap.code}
                    onPress={() => setExpandedCode(open ? null : cap.code)}
                    accessibilityRole="button"
                    accessibilityState={{ expanded: open }}
                    style={styles.capRow}
                  >
                    <View style={styles.capHead}>
                      <Text style={styles.capLabel}>{cap.label}</Text>
                      <Text style={styles.capToggle}>{open ? '−' : '+'}</Text>
                    </View>
                    {open ? <Text style={styles.capDetail}>{cap.detail}</Text> : null}
                  </Pressable>
                )
              })
            )}
          </SectionCard>
        ) : null}

        <SectionCard>
          <Text style={styles.section}>Kursy i certyfikaty</Text>
          {(therapist.courses ?? []).length === 0 ? (
            <Text style={styles.muted}>Brak wpisów.</Text>
          ) : (
            therapist.courses.map((course) => (
              <Text key={course} style={styles.course}>
                · {course}
              </Text>
            ))
          )}
        </SectionCard>

        <SectionCard>
          <LocationMapCard address={therapist.location_address || ''} title="Lokalizacja gabinetu" />
        </SectionCard>

        <SectionCard>
          <Text style={styles.section}>Kontakt</Text>
          <Button
            title="Zadzwoń"
            disabled={!therapist.phone}
            onPress={() => {
              if (therapist.phone) {
                void Linking.openURL(`tel:${therapist.phone}`)
              }
            }}
          />
          <Button
            title="Napisz SMS"
            variant="secondary"
            disabled={!therapist.phone}
            onPress={() => {
              if (therapist.phone) {
                void Linking.openURL(`sms:${therapist.phone}`)
              }
            }}
          />
          {!therapist.phone ? (
            <Text style={styles.muted}>Terapeuta nie podał numeru telefonu.</Text>
          ) : null}
        </SectionCard>
      </ScrollView>
    </>
  )
}

const styles = StyleSheet.create({
  flex: { flex: 1, backgroundColor: colors.bg },
  content: { padding: space.lg, gap: space.base, paddingBottom: space['4xl'] },
  pad: { padding: space.lg },
  hero: { flexDirection: 'row', gap: space.base, alignItems: 'flex-start' },
  heroText: { flex: 1, gap: space.sm },
  avatarClip: {
    width: 72,
    height: 72,
    borderRadius: 36,
    overflow: 'hidden',
    backgroundColor: colors.primarySubtle,
  },
  avatar: {
    width: 72,
    height: 72,
    borderRadius: 36,
    backgroundColor: colors.primarySubtle,
  },
  avatarPlaceholder: { alignItems: 'center', justifyContent: 'center' },
  initials: { fontSize: typography.xl, fontWeight: '800', color: colors.primary },
  name: { fontSize: typography['2xl'], fontWeight: '800', color: colors.ink },
  qualification: {
    fontSize: typography.sm,
    fontWeight: '700',
    color: colors.primary,
  },
  bio: { fontSize: typography.base, color: colors.ink, lineHeight: 22 },
  section: {
    fontSize: typography.sm,
    fontWeight: '700',
    color: colors.muted,
    textTransform: 'uppercase',
  },
  chipRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: space.sm,
    marginTop: space.sm,
  },
  chip: {
    paddingHorizontal: 10,
    paddingVertical: 5,
    borderRadius: radius.sm,
    borderWidth: 1,
    borderColor: colors.border,
    backgroundColor: colors.surfaceMuted,
    color: colors.muted,
    fontSize: typography.xs,
    fontWeight: '700',
    overflow: 'hidden',
  },
  chipOk: {
    borderColor: colors.primary,
    backgroundColor: colors.primarySubtle,
    color: colors.ink,
  },
  capRow: {
    marginTop: space.sm,
    paddingVertical: space.sm,
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: colors.border,
  },
  capHead: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    justifyContent: 'space-between',
    gap: space.sm,
  },
  capLabel: {
    flex: 1,
    fontSize: typography.base,
    fontWeight: '600',
    color: colors.ink,
    lineHeight: 22,
  },
  capToggle: {
    fontSize: typography.lg,
    color: colors.muted,
    fontWeight: '500',
    lineHeight: 22,
  },
  capDetail: {
    marginTop: space.sm,
    fontSize: typography.sm,
    color: colors.muted,
    lineHeight: 20,
  },
  course: { fontSize: typography.base, color: colors.ink },
  link: {
    fontSize: typography.base,
    color: colors.primary,
    fontWeight: '600',
    textDecorationLine: 'underline',
  },
  muted: { fontSize: typography.sm, color: colors.muted },
})
