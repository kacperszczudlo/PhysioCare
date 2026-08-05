import { Stack, useLocalSearchParams } from 'expo-router'
import { useCallback, useEffect, useState } from 'react'
import { Linking, ScrollView, StyleSheet, Text, View } from 'react-native'

import { getErrorMessage } from '@/api/client'
import { patientApi } from '@/api/patient'
import type { TherapistPublic } from '@/api/types'
import { ErrorBanner, LoadingBlock } from '@/components/AsyncState'
import { Button } from '@/components/Button'
import { SectionCard } from '@/components/ScreenHeader'
import { colors, space, typography } from '@/theme/tokens'

export default function TherapistPublicScreen() {
  const { id } = useLocalSearchParams<{ id: string }>()
  const [therapist, setTherapist] = useState<TherapistPublic | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const load = useCallback(async () => {
    if (!id) {
      return
    }
    setError(null)
    setLoading(true)
    try {
      setTherapist(await patientApi.getTherapistPublic(id))
    } catch (err) {
      setError(getErrorMessage(err, 'Nie udało się pobrać profilu terapeuty.'))
    } finally {
      setLoading(false)
    }
  }, [id])

  useEffect(() => {
    void load()
  }, [load])

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

  return (
    <>
      <Stack.Screen options={{ title: fullName }} />
      <ScrollView style={styles.flex} contentContainerStyle={styles.content}>
        {error ? <ErrorBanner message={error} onRetry={() => void load()} /> : null}

        <SectionCard>
          <Text style={styles.name}>{fullName}</Text>
          <Text style={styles.bio}>{therapist.bio || 'Brak biogramu.'}</Text>
        </SectionCard>

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
  name: { fontSize: typography['2xl'], fontWeight: '800', color: colors.ink },
  bio: { fontSize: typography.base, color: colors.ink, lineHeight: 22 },
  section: {
    fontSize: typography.sm,
    fontWeight: '700',
    color: colors.muted,
    textTransform: 'uppercase',
  },
  course: { fontSize: typography.base, color: colors.ink },
  muted: { fontSize: typography.sm, color: colors.muted },
})
