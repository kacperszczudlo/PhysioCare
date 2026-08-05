import { Stack, useLocalSearchParams, useRouter } from 'expo-router'
import { useCallback, useEffect, useMemo, useState } from 'react'
import { Linking, Pressable, ScrollView, StyleSheet, Text, View } from 'react-native'

import { getErrorMessage } from '@/api/client'
import { patientApi } from '@/api/patient'
import type { TodayExercise } from '@/api/types'
import { ErrorBanner, LoadingBlock } from '@/components/AsyncState'
import { Button } from '@/components/Button'
import { ExerciseVideoPlayer } from '@/components/ExerciseVideoPlayer'
import { SectionCard } from '@/components/ScreenHeader'
import { todayISODate } from '@/lib/format'
import { resolveMediaUrl } from '@/lib/mediaUrl'
import { colors, radius, space, typography } from '@/theme/tokens'

export default function ExerciseDetailScreen() {
  const { id } = useLocalSearchParams<{ id: string }>()
  const router = useRouter()
  const [item, setItem] = useState<TodayExercise | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)
  const [mediaError, setMediaError] = useState<string | null>(null)

  const mediaUrl = useMemo(
    () => (item ? resolveMediaUrl(item.exercise_file_url) : null),
    [item],
  )

  const load = useCallback(async () => {
    if (!id) {
      return
    }
    setLoading(true)
    setError(null)
    try {
      const list = await patientApi.getExercisesToday()
      const found = list.find((ex) => ex.id === id) ?? null
      setItem(found)
      if (!found) {
        setError('Nie znaleziono tego zalecenia na dziś.')
      }
    } catch (err) {
      setError(getErrorMessage(err, 'Nie udało się pobrać ćwiczenia.'))
      setItem(null)
    } finally {
      setLoading(false)
    }
  }, [id])

  useEffect(() => {
    void load()
  }, [load])

  async function onToggleDone() {
    if (!item || busy) {
      return
    }
    const previous = item.completed_today
    const nextDone = !previous
    setBusy(true)
    setItem({ ...item, completed_today: nextDone })
    try {
      await patientApi.completeExercise(item.id, todayISODate(), nextDone)
    } catch (err) {
      setItem({ ...item, completed_today: previous })
      setError(getErrorMessage(err, 'Nie udało się zaktualizować zalecenia.'))
    } finally {
      setBusy(false)
    }
  }

  async function openPdf() {
    if (!mediaUrl) {
      setMediaError('Brak pliku ćwiczenia.')
      return
    }
    setMediaError(null)
    const supported = await Linking.canOpenURL(mediaUrl)
    if (!supported) {
      setMediaError('Nie można otworzyć PDF na urządzeniu.')
      return
    }
    await Linking.openURL(mediaUrl)
  }

  if (loading) {
    return <LoadingBlock label="Ładowanie ćwiczenia…" />
  }

  return (
    <>
      <Stack.Screen options={{ title: item?.exercise_title ?? 'Ćwiczenie' }} />
      <ScrollView style={styles.flex} contentContainerStyle={styles.content}>
        {error ? <ErrorBanner message={error} onRetry={() => void load()} /> : null}

        {!item ? (
          <Button title="Wróć do pulpitu" onPress={() => router.back()} />
        ) : (
          <>
            <SectionCard>
              <View style={styles.headerRow}>
                <View style={styles.headerText}>
                  <Text style={styles.title}>{item.exercise_title}</Text>
                  <Text style={styles.dosage}>{item.dosage}</Text>
                </View>
                <Pressable
                  onPress={() => void onToggleDone()}
                  disabled={busy}
                  style={[styles.check, item.completed_today ? styles.checkOn : null]}
                  accessibilityRole="checkbox"
                  accessibilityLabel="Oznacz jako wykonane"
                  accessibilityState={{ checked: item.completed_today, busy }}
                  hitSlop={8}
                >
                  {item.completed_today ? <Text style={styles.checkMark}>✓</Text> : null}
                </Pressable>
              </View>
              <Text style={styles.hint}>
                Zielone kółko oznacza wykonanie na dziś. Instrukcję i materiał masz poniżej.
              </Text>
            </SectionCard>

            <Text style={styles.sectionLabel}>Instrukcja</Text>
            <SectionCard>
              {item.exercise_instruction?.trim() ? (
                <Text style={styles.instruction}>{item.exercise_instruction}</Text>
              ) : (
                <Text style={styles.muted}>Terapeuta nie dodał opisu tekstowego.</Text>
              )}
            </SectionCard>

            <Text style={styles.sectionLabel}>Materiał</Text>
            <SectionCard>
              <View style={styles.mediaBadge}>
                <Text style={styles.mediaBadgeText}>
                  {item.exercise_media_type === 'VIDEO' ? 'Wideo' : 'PDF'}
                </Text>
              </View>

              {item.exercise_media_type === 'VIDEO' ? (
                mediaUrl ? (
                  <ExerciseVideoPlayer uri={mediaUrl} />
                ) : (
                  <Text style={styles.mediaError}>Brak pliku wideo.</Text>
                )
              ) : (
                <>
                  <Text style={styles.muted}>Karta PDF z opisem ruchu.</Text>
                  {mediaError ? <Text style={styles.mediaError}>{mediaError}</Text> : null}
                  <Button
                    title="Otwórz PDF"
                    onPress={() => void openPdf()}
                    style={{ marginTop: space.md }}
                  />
                </>
              )}
            </SectionCard>

            <Text style={styles.period}>
              Okres: {item.start_date} – {item.end_date}
            </Text>
          </>
        )}
      </ScrollView>
    </>
  )
}

const styles = StyleSheet.create({
  flex: { flex: 1, backgroundColor: colors.bg },
  content: { padding: space.lg, paddingBottom: space['4xl'], gap: space.md },
  headerRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: space.md,
  },
  headerText: { flex: 1, gap: 4 },
  title: { fontSize: typography.xl, fontWeight: '700', color: colors.ink },
  dosage: { fontSize: typography.sm, color: colors.muted, fontWeight: '600' },
  hint: { marginTop: space.md, fontSize: typography.sm, color: colors.muted, lineHeight: 20 },
  sectionLabel: {
    marginTop: space.sm,
    fontSize: typography.sm,
    fontWeight: '700',
    color: colors.muted,
    textTransform: 'uppercase',
    letterSpacing: 0.4,
  },
  instruction: {
    fontSize: typography.base,
    color: colors.ink,
    lineHeight: 24,
  },
  muted: { fontSize: typography.sm, color: colors.muted, lineHeight: 20 },
  mediaBadge: {
    alignSelf: 'flex-start',
    backgroundColor: colors.primarySubtle,
    paddingHorizontal: space.sm,
    paddingVertical: 4,
    borderRadius: radius.sm,
    marginBottom: space.sm,
  },
  mediaBadgeText: {
    fontSize: typography.xs,
    fontWeight: '700',
    color: colors.primary,
    textTransform: 'uppercase',
    letterSpacing: 0.4,
  },
  mediaError: { color: colors.danger, fontSize: typography.sm },
  check: {
    width: 36,
    height: 36,
    borderRadius: 18,
    borderWidth: 1.5,
    borderColor: colors.borderStrong,
    alignItems: 'center',
    justifyContent: 'center',
  },
  checkOn: { backgroundColor: colors.success, borderColor: colors.success },
  checkMark: { color: colors.onPrimary, fontWeight: '700', fontSize: 18 },
  period: { fontSize: typography.sm, color: colors.faint, marginTop: space.sm },
})
