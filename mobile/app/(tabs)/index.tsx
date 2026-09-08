import { useFocusEffect, useRouter } from 'expo-router'
import { useCallback, useEffect, useRef, useState } from 'react'
import { Pressable, RefreshControl, ScrollView, StyleSheet, Text, View } from 'react-native'

import { getErrorMessage } from '@/api/client'
import { patientApi } from '@/api/patient'
import type { TodayExercise, Visit } from '@/api/types'
import { useAuth } from '@/auth/AuthContext'
import { EmptyState, ErrorBanner, LoadingBlock } from '@/components/AsyncState'
import { BrandMark } from '@/components/BrandMark'
import { ScreenHeader, SectionCard } from '@/components/ScreenHeader'
import { formatDateTime, formatTimeRange } from '@/lib/format'
import { isDashboardRealtimeEvent } from '@/realtime/types'
import { useRealtimeEvents } from '@/realtime/useRealtimeEvents'
import { useSilentPoll } from '@/realtime/useSilentPoll'
import { colors, controlSize, radius, space, typography } from '@/theme/tokens'

export default function DashboardScreen() {
  const { user } = useAuth()
  const router = useRouter()
  const [visits, setVisits] = useState<Visit[]>([])
  const [exercises, setExercises] = useState<TodayExercise[]>([])
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [busyId, setBusyId] = useState<string | null>(null)
  const softReloadTimer = useRef<ReturnType<typeof setTimeout> | null>(null)

  const load = useCallback(async (opts?: { silent?: boolean }) => {
    if (!opts?.silent) {
      setError(null)
    }
    try {
      const [upcoming, today] = await Promise.all([
        patientApi.getVisits('upcoming'),
        patientApi.getExercisesToday(),
      ])
      setVisits(upcoming)
      setExercises(today)
      if (opts?.silent) {
        setError(null)
      }
    } catch (err) {
      if (!opts?.silent) {
        setError(getErrorMessage(err, 'Nie udało się pobrać pulpitu.'))
      }
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

  useRealtimeEvents(
    useCallback(
      (event) => {
        if (!isDashboardRealtimeEvent(event)) {
          return
        }
        if (softReloadTimer.current != null) {
          clearTimeout(softReloadTimer.current)
        }
        softReloadTimer.current = setTimeout(() => {
          softReloadTimer.current = null
          void load({ silent: true })
        }, 250)
      },
      [load],
    ),
  )

  useSilentPoll(
    useCallback(() => {
      void load({ silent: true })
    }, [load]),
  )

  useEffect(() => {
    return () => {
      if (softReloadTimer.current != null) {
        clearTimeout(softReloadTimer.current)
      }
    }
  }, [])

  async function onToggleExercise(item: TodayExercise) {
    if (busyId) {
      return
    }
    const nextDone = !item.completed_today
    setBusyId(item.id)
    setExercises((prev) =>
      prev.map((ex) => (ex.id === item.id ? { ...ex, completed_today: nextDone } : ex)),
    )
    try {
      await patientApi.completeExercise(item.id, undefined, nextDone)
    } catch (err) {
      setExercises((prev) =>
        prev.map((ex) =>
          ex.id === item.id ? { ...ex, completed_today: item.completed_today } : ex,
        ),
      )
      setError(getErrorMessage(err, 'Nie udało się zaktualizować zalecenia.'))
    } finally {
      setBusyId(null)
    }
  }

  const nextVisit = visits[0] ?? null
  const doneCount = exercises.filter((e) => e.completed_today).length

  if (loading) {
    return <LoadingBlock label="Ładowanie pulpitu…" />
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
      <BrandMark variant="sygnet" size="sm" style={styles.brand} />
      <ScreenHeader
        title={`Cześć, ${user?.first_name ?? 'Pacjencie'}`}
        subtitle="Najbliższa wizyta i zalecenia na dziś."
      />

      {error ? <ErrorBanner message={error} onRetry={() => void load()} /> : null}

      <Text style={styles.sectionLabel}>Najbliższa wizyta</Text>
      {nextVisit ? (
        <Pressable onPress={() => router.push(`/visit/${nextVisit.id}`)}>
          <SectionCard>
            <View style={styles.rowBetween}>
              <Text style={styles.cardTitle}>{nextVisit.therapy_type_name}</Text>
              <View
                style={[
                  styles.dot,
                  { backgroundColor: nextVisit.therapy_type_color || colors.primary },
                ]}
              />
            </View>
            <Text style={styles.meta}>{formatDateTime(nextVisit.start_at)}</Text>
            <Text style={styles.meta}>
              {formatTimeRange(nextVisit.start_at, nextVisit.end_at)} ·{' '}
              {nextVisit.therapist_first_name} {nextVisit.therapist_last_name}
            </Text>
            {nextVisit.location_address ? (
              <Text style={styles.muted}>{nextVisit.location_address}</Text>
            ) : null}
          </SectionCard>
        </Pressable>
      ) : (
        <EmptyState
          title="Brak nadchodzących wizyt"
          description="Gdy terapeuta umówi termin, pojawi się tutaj."
        />
      )}

      <View style={styles.rowBetween}>
        <Text style={styles.sectionLabel}>Zalecenia na dziś</Text>
        <Text style={styles.progress}>
          {doneCount}/{exercises.length}
        </Text>
      </View>

      {exercises.length === 0 ? (
        <EmptyState
          title="Brak ćwiczeń na dziś"
          description="Przypisane zalecenia pokażą się w okresie ich obowiązywania."
        />
      ) : (
        <View style={styles.list}>
          {exercises.map((item) => (
            <View
              key={item.id}
              style={[styles.exercise, item.completed_today ? styles.exerciseDone : null]}
            >
              <Pressable
                onPress={() => void onToggleExercise(item)}
                disabled={busyId === item.id}
                style={[styles.check, item.completed_today ? styles.checkOn : null]}
                accessibilityRole="checkbox"
                accessibilityLabel={`Oznacz ${item.exercise_title} jako wykonane`}
                accessibilityState={{ checked: item.completed_today, busy: busyId === item.id }}
              >
                {item.completed_today ? <Text style={styles.checkMark}>✓</Text> : null}
              </Pressable>
              <Pressable
                style={styles.exerciseBody}
                onPress={() =>
                  router.push({ pathname: '/exercise/[id]', params: { id: item.id } })
                }
                accessibilityRole="button"
                accessibilityLabel={`Szczegóły: ${item.exercise_title}`}
              >
                <Text style={[styles.cardTitle, item.completed_today ? styles.strike : null]}>
                  {item.exercise_title}
                </Text>
                <Text style={styles.muted}>{item.dosage}</Text>
                {item.categories?.length ? (
                  <View style={styles.tags}>
                    {item.categories.slice(0, 3).map((category) => (
                      <View key={category.id} style={styles.tag}>
                        <Text style={styles.tagText}>{category.name}</Text>
                      </View>
                    ))}
                    {item.categories.length > 3 ? (
                      <Text style={styles.tagMore}>+{item.categories.length - 3}</Text>
                    ) : null}
                  </View>
                ) : null}
                <Text style={styles.openHint}>Instrukcja i materiał</Text>
              </Pressable>
            </View>
          ))}
        </View>
      )}
    </ScrollView>
  )
}

const styles = StyleSheet.create({
  flex: { flex: 1, backgroundColor: colors.bg },
  content: { padding: space.lg, paddingBottom: space['4xl'], gap: space.md },
  brand: { marginBottom: space.xs },
  sectionLabel: {
    marginTop: space.md,
    fontSize: typography.sm,
    fontWeight: '700',
    color: colors.muted,
    textTransform: 'uppercase',
    letterSpacing: 0.4,
  },
  progress: { color: colors.primary, fontWeight: '700', marginTop: space.md },
  rowBetween: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  cardTitle: { fontSize: typography.lg, fontWeight: '700', color: colors.ink },
  meta: { fontSize: typography.sm, color: colors.ink },
  muted: { fontSize: typography.sm, color: colors.muted },
  openHint: {
    marginTop: 4,
    fontSize: typography.xs,
    fontWeight: '600',
    color: colors.primary,
  },
  tags: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 4,
    marginTop: 4,
  },
  tag: {
    backgroundColor: colors.primarySubtle,
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: radius.sm,
  },
  tagText: {
    fontSize: typography.xs,
    fontWeight: '600',
    color: colors.primary,
  },
  tagMore: {
    fontSize: typography.xs,
    fontWeight: '600',
    color: colors.muted,
    alignSelf: 'center',
  },
  dot: { width: 12, height: 12, borderRadius: 6 },
  list: { gap: space.md },
  exercise: {
    flexDirection: 'row',
    gap: space.md,
    alignItems: 'flex-start',
    backgroundColor: colors.surface,
    borderRadius: radius.lg,
    borderWidth: 1,
    borderColor: colors.border,
    padding: space.base,
  },
  exerciseDone: { backgroundColor: colors.successSubtle, borderColor: colors.success },
  exerciseBody: { flex: 1, gap: 4 },
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
  strike: { textDecorationLine: 'line-through', color: colors.muted },
})
