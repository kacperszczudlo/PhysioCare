import { useFocusEffect, useRouter } from 'expo-router'
import { useCallback, useEffect, useRef, useState } from 'react'
import { Pressable, RefreshControl, ScrollView, StyleSheet, Text, View } from 'react-native'

import { getErrorMessage } from '@/api/client'
import { patientApi } from '@/api/patient'
import type { Visit } from '@/api/types'
import { EmptyState, ErrorBanner, LoadingBlock } from '@/components/AsyncState'
import { MobileVisitsSkeleton } from '@/components/skeletons/MobileSkeletons'
import { Button } from '@/components/Button'
import { ScreenHeader } from '@/components/ScreenHeader'
import { formatDateTime, formatTimeRange, visitStatusLabel } from '@/lib/format'
import { isVisitRealtimeEvent } from '@/realtime/types'
import { useRealtimeEvents } from '@/realtime/useRealtimeEvents'
import { useSilentPoll } from '@/realtime/useSilentPoll'
import { colors, controlSize, radius, space, typography } from '@/theme/tokens'

type TabKey = 'upcoming' | 'past'

export default function VisitsScreen() {
  const router = useRouter()
  const [tab, setTab] = useState<TabKey>('upcoming')
  const [visits, setVisits] = useState<Visit[]>([])
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const tabRef = useRef(tab)
  tabRef.current = tab
  const softReloadTimer = useRef<ReturnType<typeof setTimeout> | null>(null)

  const load = useCallback(async (status: TabKey, opts?: { silent?: boolean }) => {
    if (!opts?.silent) {
      setError(null)
    }
    try {
      const data = await patientApi.getVisits(status)
      setVisits(data)
      if (opts?.silent) {
        setError(null)
      }
    } catch (err) {
      if (!opts?.silent) {
        setError(getErrorMessage(err, 'Nie udało się pobrać wizyt.'))
      }
    } finally {
      setLoading(false)
      setRefreshing(false)
    }
  }, [])

  useFocusEffect(
    useCallback(() => {
      setLoading(true)
      void load(tab)
    }, [load, tab]),
  )

  useRealtimeEvents(
    useCallback(
      (event) => {
        if (!isVisitRealtimeEvent(event)) {
          return
        }
        if (softReloadTimer.current != null) {
          clearTimeout(softReloadTimer.current)
        }
        softReloadTimer.current = setTimeout(() => {
          softReloadTimer.current = null
          void load(tabRef.current, { silent: true })
        }, 250)
      },
      [load],
    ),
  )

  useSilentPoll(
    useCallback(() => {
      void load(tabRef.current, { silent: true })
    }, [load]),
  )

  useEffect(() => {
    return () => {
      if (softReloadTimer.current != null) {
        clearTimeout(softReloadTimer.current)
      }
    }
  }, [])

  function switchTab(next: TabKey) {
    if (next === tab) {
      return
    }
    setTab(next)
    setLoading(true)
  }

  return (
    <View style={styles.flex}>
      <View style={styles.pad}>
        <ScreenHeader title="Wizyty" subtitle="Nadchodzące, zgłoszenia i archiwum." />
        <Button title="Umów wizytę" onPress={() => router.push('/visit/request')} />
        <View style={styles.tabs}>
          <Segment
            label="Nadchodzące"
            active={tab === 'upcoming'}
            onPress={() => switchTab('upcoming')}
          />
          <Segment label="Archiwum" active={tab === 'past'} onPress={() => switchTab('past')} />
        </View>
      </View>

      {loading ? (
        <LoadingBlock skeleton={<MobileVisitsSkeleton />} />
      ) : (
        <ScrollView
          contentContainerStyle={styles.list}
          refreshControl={
            <RefreshControl
              refreshing={refreshing}
              onRefresh={() => {
                setRefreshing(true)
                void load(tab)
              }}
              tintColor={colors.primary}
            />
          }
        >
          {error ? <ErrorBanner message={error} onRetry={() => void load(tab)} /> : null}

          {visits.length === 0 ? (
            <EmptyState
              title={tab === 'upcoming' ? 'Brak nadchodzących wizyt' : 'Brak historii wizyt'}
              description={
                tab === 'upcoming'
                  ? 'Wyślij zgłoszenie przyciskiem powyżej - fizjoterapeuta zatwierdzi termin.'
                  : undefined
              }
            />
          ) : (
            visits.map((visit) => (
              <Pressable
                key={visit.id}
                onPress={() => router.push(`/visit/${visit.id}`)}
                style={[
                  styles.card,
                  visit.status === 'PENDING_APPROVAL' ? styles.cardPending : null,
                ]}
              >
                <View style={styles.rowBetween}>
                  <Text style={styles.title}>{visit.therapy_type_name}</Text>
                  <Text
                    style={[
                      styles.status,
                      visit.status === 'PENDING_APPROVAL' ? styles.statusPending : null,
                    ]}
                  >
                    {visitStatusLabel(visit.status)}
                  </Text>
                </View>
                <Text style={styles.meta}>{formatDateTime(visit.start_at)}</Text>
                <Text style={styles.muted}>
                  {formatTimeRange(visit.start_at, visit.end_at)} · {visit.therapist_first_name}{' '}
                  {visit.therapist_last_name}
                </Text>
              </Pressable>
            ))
          )}
        </ScrollView>
      )}
    </View>
  )
}

function Segment({
  label,
  active,
  onPress,
}: {
  label: string
  active: boolean
  onPress: () => void
}) {
  return (
    <Pressable
      onPress={onPress}
      style={[styles.segment, active ? styles.segmentOn : null]}
      accessibilityRole="tab"
      accessibilityState={{ selected: active }}
    >
      <Text style={[styles.segmentLabel, active ? styles.segmentLabelOn : null]}>{label}</Text>
    </Pressable>
  )
}

const styles = StyleSheet.create({
  flex: { flex: 1, backgroundColor: colors.bg },
  pad: { paddingHorizontal: space.lg, paddingTop: space.sm, gap: space.md },
  tabs: {
    flexDirection: 'row',
    backgroundColor: colors.surfaceMuted,
    borderRadius: radius.md,
    padding: 4,
    gap: 4,
    marginBottom: space.md,
  },
  segment: {
    flex: 1,
    minHeight: controlSize,
    borderRadius: radius.sm,
    alignItems: 'center',
    justifyContent: 'center',
  },
  segmentOn: { backgroundColor: colors.surface },
  segmentLabel: { color: colors.muted, fontWeight: '600', fontSize: typography.sm },
  segmentLabelOn: { color: colors.ink },
  list: { padding: space.lg, gap: space.md, paddingBottom: space['4xl'] },
  card: {
    backgroundColor: colors.surface,
    borderRadius: radius.lg,
    borderWidth: 1,
    borderColor: colors.border,
    padding: space.base,
    gap: space.xs,
  },
  cardPending: {
    borderStyle: 'dashed',
    borderColor: colors.primary,
  },
  rowBetween: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    gap: space.sm,
  },
  title: { flex: 1, fontSize: typography.lg, fontWeight: '700', color: colors.ink },
  status: { fontSize: typography.xs, color: colors.primary, fontWeight: '700', maxWidth: '46%' },
  statusPending: { color: colors.warning },
  meta: { fontSize: typography.sm, color: colors.ink },
  muted: { fontSize: typography.sm, color: colors.muted },
})
