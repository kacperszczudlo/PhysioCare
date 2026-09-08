import { Stack, useLocalSearchParams, useRouter } from 'expo-router'
import { useCallback, useEffect, useState } from 'react'
import { Linking, Pressable, ScrollView, StyleSheet, Text, View } from 'react-native'

import { getErrorMessage } from '@/api/client'
import { patientApi } from '@/api/patient'
import type { CategoryKind, TodayExercise } from '@/api/types'
import { ErrorBanner, LoadingBlock } from '@/components/AsyncState'
import { Button } from '@/components/Button'
import { ExerciseVideoPlayer } from '@/components/ExerciseVideoPlayer'
import { SectionCard } from '@/components/ScreenHeader'
import { downloadAuthenticatedMediaToCache, useAuthenticatedMediaSource } from '@/lib/authMedia'
import { colors, controlSize, radius, space, typography } from '@/theme/tokens'

function tagStyleForKind(kind: CategoryKind) {
  switch (kind) {
    case 'TYPE':
      return styles.tagType
    case 'REGION':
      return styles.tagRegion
    case 'MUSCLE':
      return styles.tagMuscle
    case 'INJURY':
      return styles.tagInjury
    default:
      return null
  }
}

function tagTextForKind(kind: CategoryKind) {
  switch (kind) {
    case 'TYPE':
      return styles.tagTextType
    case 'REGION':
      return styles.tagTextRegion
    case 'MUSCLE':
      return styles.tagTextMuscle
    case 'INJURY':
      return styles.tagTextInjury
    default:
      return null
  }
}

export default function ExerciseDetailScreen() {
  const { id } = useLocalSearchParams<{ id: string }>()
  const router = useRouter()
  const [item, setItem] = useState<TodayExercise | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)
  const [mediaError, setMediaError] = useState<string | null>(null)

  const { source: mediaSource } = useAuthenticatedMediaSource(item?.exercise_file_url)

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
      await patientApi.completeExercise(item.id, undefined, nextDone)
    } catch (err) {
      setItem({ ...item, completed_today: previous })
      setError(getErrorMessage(err, 'Nie udało się zaktualizować zalecenia.'))
    } finally {
      setBusy(false)
    }
  }

  async function openPdf() {
    if (!item?.exercise_file_url) {
      setMediaError('Brak pliku ćwiczenia.')
      return
    }
    setMediaError(null)
    try {
      const localUri = await downloadAuthenticatedMediaToCache(
        item.exercise_file_url,
        'exercise.pdf',
      )
      if (!localUri) {
        setMediaError('Nie można pobrać PDF.')
        return
      }
      const supported = await Linking.canOpenURL(localUri)
      if (!supported) {
        setMediaError('Nie można otworzyć PDF na urządzeniu.')
        return
      }
      await Linking.openURL(localUri)
    } catch {
      setMediaError('Nie udało się otworzyć PDF.')
    }
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
                >
                  {item.completed_today ? <Text style={styles.checkMark}>✓</Text> : null}
                </Pressable>
              </View>
              {item.categories?.length ? (
                <View style={styles.tags}>
                  {item.categories.map((category) => (
                    <View key={category.id} style={[styles.tag, tagStyleForKind(category.kind)]}>
                      <Text style={[styles.tagText, tagTextForKind(category.kind)]}>
                        {category.name}
                      </Text>
                    </View>
                  ))}
                </View>
              ) : null}
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
                mediaSource ? (
                  <ExerciseVideoPlayer source={mediaSource} />
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
              Okres: {item.start_date} - {item.end_date}
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
  tags: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 6,
    marginTop: space.md,
  },
  tag: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: radius.sm,
    backgroundColor: colors.primarySubtle,
  },
  tagText: {
    fontSize: typography.xs,
    fontWeight: '700',
    color: colors.primary,
  },
  tagType: { backgroundColor: '#e4f3e8' },
  tagRegion: { backgroundColor: '#e4eef8' },
  tagMuscle: { backgroundColor: '#f8eee0' },
  tagInjury: { backgroundColor: '#f8e6e4' },
  tagTextType: { color: '#2f6b3c' },
  tagTextRegion: { color: '#2f4f7a' },
  tagTextMuscle: { color: '#7a4f20' },
  tagTextInjury: { color: '#8a3530' },
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
    width: controlSize,
    height: controlSize,
    borderRadius: radius.md,
    borderWidth: 1.5,
    borderColor: colors.borderStrong,
    alignItems: 'center',
    justifyContent: 'center',
  },
  checkOn: { backgroundColor: colors.success, borderColor: colors.success },
  checkMark: { color: colors.onPrimary, fontWeight: '700', fontSize: typography.lg },
  period: { fontSize: typography.sm, color: colors.faint, marginTop: space.sm },
})
