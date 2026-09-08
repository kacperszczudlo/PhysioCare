import { useFocusEffect } from 'expo-router'
import { useCallback, useEffect, useRef, useState } from 'react'
import {
  Linking,
  Pressable,
  RefreshControl,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from 'react-native'

import { getErrorMessage } from '@/api/client'
import { patientApi } from '@/api/patient'
import type { ClinicalDocumentItem, ClinicalDocumentKind } from '@/api/types'
import { EmptyState, ErrorBanner, LoadingBlock } from '@/components/AsyncState'
import { ScreenHeader } from '@/components/ScreenHeader'
import { downloadAuthenticatedMediaToCache } from '@/lib/authMedia'
import { formatDate } from '@/lib/format'
import { isDocumentRealtimeEvent } from '@/realtime/types'
import { useRealtimeEvents } from '@/realtime/useRealtimeEvents'
import { useSilentPoll } from '@/realtime/useSilentPoll'
import { colors, controlSize, radius, space, typography } from '@/theme/tokens'

type FilterKey = 'all' | ClinicalDocumentKind

const FILTERS: { key: FilterKey; label: string }[] = [
  { key: 'all', label: 'Wszystkie' },
  { key: 'recommendation', label: 'Kierowanie' },
  { key: 'device_order', label: 'Wyroby' },
  { key: 'recepta_na_ruch', label: 'Recepta' },
  { key: 'refusal', label: 'Odmowy' },
  { key: 'pdf', label: 'PDF' },
]

function detailText(value: unknown): string {
  if (typeof value === 'string') {
    return value
  }
  if (typeof value === 'boolean') {
    return value ? 'Tak' : 'Nie'
  }
  if (typeof value === 'number') {
    return String(value)
  }
  return ''
}

export default function DocumentsScreen() {
  const [filter, setFilter] = useState<FilterKey>('all')
  const [items, setItems] = useState<ClinicalDocumentItem[]>([])
  const [expandedId, setExpandedId] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const filterRef = useRef(filter)
  filterRef.current = filter
  const softReloadTimer = useRef<ReturnType<typeof setTimeout> | null>(null)

  const load = useCallback(async (next: FilterKey, opts?: { silent?: boolean }) => {
    if (!opts?.silent) {
      setError(null)
    }
    try {
      const data = await patientApi.getClinicalDocuments(next === 'all' ? undefined : next)
      setItems(data)
      if (opts?.silent) {
        setError(null)
      }
    } catch (err) {
      if (!opts?.silent) {
        setError(getErrorMessage(err, 'Nie udało się pobrać dokumentacji.'))
      }
    } finally {
      setLoading(false)
      setRefreshing(false)
    }
  }, [])

  useFocusEffect(
    useCallback(() => {
      setLoading(true)
      void load(filter)
    }, [filter, load]),
  )

  useRealtimeEvents(
    useCallback(
      (event) => {
        if (!isDocumentRealtimeEvent(event)) {
          return
        }
        if (softReloadTimer.current != null) {
          clearTimeout(softReloadTimer.current)
        }
        softReloadTimer.current = setTimeout(() => {
          softReloadTimer.current = null
          void load(filterRef.current, { silent: true })
        }, 250)
      },
      [load],
    ),
  )

  useSilentPoll(
    useCallback(() => {
      void load(filterRef.current, { silent: true })
    }, [load]),
  )

  useEffect(() => {
    return () => {
      if (softReloadTimer.current != null) {
        clearTimeout(softReloadTimer.current)
      }
    }
  }, [])

  function switchFilter(next: FilterKey) {
    if (next === filter) {
      return
    }
    setFilter(next)
    setExpandedId(null)
    setLoading(true)
  }

  return (
    <View style={styles.flex}>
      <View style={styles.pad}>
        <ScreenHeader
          title="Dokumentacja"
          subtitle="Dokumenty wystawione przez fizjoterapeutę — dostępne od razu po utworzeniu."
        />
        <ScrollView
          horizontal
          showsHorizontalScrollIndicator={false}
          contentContainerStyle={styles.filters}
        >
          {FILTERS.map((item) => (
            <Segment
              key={item.key}
              label={item.label}
              active={filter === item.key}
              onPress={() => switchFilter(item.key)}
            />
          ))}
        </ScrollView>
      </View>

      {loading ? (
        <LoadingBlock />
      ) : (
        <ScrollView
          contentContainerStyle={styles.list}
          refreshControl={
            <RefreshControl
              refreshing={refreshing}
              onRefresh={() => {
                setRefreshing(true)
                void load(filter)
              }}
              tintColor={colors.primary}
            />
          }
        >
          {error ? <ErrorBanner message={error} onRetry={() => void load(filter)} /> : null}

          {items.length === 0 ? (
            <EmptyState
              title="Brak dokumentów"
              description="Gdy fizjoterapeuta wystawi kierowanie, wyrób, Receptę na Ruch lub PDF — pojawią się tutaj."
            />
          ) : (
            items.map((doc) => {
              const open = expandedId === `${doc.kind}:${doc.id}`
              return (
                <DocumentCard
                  key={`${doc.kind}:${doc.id}`}
                  doc={doc}
                  expanded={open}
                  onToggle={() => setExpandedId(open ? null : `${doc.kind}:${doc.id}`)}
                />
              )
            })
          )}
        </ScrollView>
      )}
    </View>
  )
}

function DocumentCard({
  doc,
  expanded,
  onToggle,
}: {
  doc: ClinicalDocumentItem
  expanded: boolean
  onToggle: () => void
}) {
  async function openPdf() {
    if (!doc.file_url) {
      return
    }
    const localUri = await downloadAuthenticatedMediaToCache(doc.file_url, 'clinical.pdf')
    if (localUri) {
      await Linking.openURL(localUri)
    }
  }

  return (
    <Pressable
      onPress={onToggle}
      style={[styles.card, doc.kind === 'refusal' ? styles.cardRefusal : null]}
      accessibilityRole="button"
      accessibilityState={{ expanded }}
      accessibilityLabel={`${doc.kind_label}: ${doc.title}`}
    >
      <View style={styles.rowBetween}>
        <Text style={styles.kind}>{doc.kind_label}</Text>
        <Text style={styles.date}>{formatDate(doc.created_at)}</Text>
      </View>
      <Text style={styles.title}>{doc.title}</Text>
      <Text style={styles.summary}>{doc.summary}</Text>
      <Text style={styles.meta}>{doc.therapist_name}</Text>

      {expanded ? (
        <View style={styles.details}>
          <DetailRows doc={doc} />
          {doc.kind === 'pdf' && doc.file_url ? (
            <Pressable
              onPress={() => void openPdf()}
              style={styles.pdfBtn}
              accessibilityRole="link"
              accessibilityLabel="Otwórz plik PDF"
            >
              <Text style={styles.pdfBtnLabel}>Otwórz PDF</Text>
            </Pressable>
          ) : null}
        </View>
      ) : (
        <Text style={styles.hint}>Dotknij, aby zobaczyć szczegóły</Text>
      )}
    </Pressable>
  )
}

function DetailRows({ doc }: { doc: ClinicalDocumentItem }) {
  const d = doc.details
  const rows: { label: string; value: string }[] = []

  if (doc.kind === 'recommendation') {
    pushRow(rows, 'Specjalizacja', d.target_specialty)
    pushRow(rows, 'Obszar', d.body_area)
    pushRow(rows, 'Uzasadnienie', d.justification)
    pushRow(rows, 'Czerwone flagi', d.red_flags_noted)
    pushRow(rows, 'Finansowanie', d.funding_hint_label)
    pushRow(rows, 'Uwaga', d.disclaimer)
  } else if (doc.kind === 'device_order') {
    pushRow(rows, 'Kod', d.device_code)
    pushRow(rows, 'Grupa', d.device_group)
    pushRow(rows, 'Strona', d.side_label)
    pushRow(rows, 'Ilość', d.quantity)
    pushRow(rows, 'ICD-10', d.icd10_code)
    pushRow(rows, 'Notatka', d.notes)
    pushRow(rows, 'Uwaga', d.disclaimer)
  } else if (doc.kind === 'refusal') {
    pushRow(rows, 'Informacja', d.patient_notice)
    pushRow(rows, 'Zlecenie', d.physician_order_description)
    pushRow(rows, 'Uzasadnienie', d.refusal_reason)
    pushRow(rows, 'Powiadomiono lekarza', d.physician_notified)
  } else if (doc.kind === 'recepta_na_ruch') {
    pushRow(rows, 'Gotowość', d.readiness_confirmed)
    pushRow(rows, 'Aktywność', d.activity_notes)
    pushRow(rows, 'Następny krok', d.next_step)
  } else if (doc.kind === 'pdf') {
    pushRow(rows, 'Typ pliku', d.mime_type)
  }

  return (
    <View style={styles.detailList}>
      {rows.map((row) => (
        <View key={row.label} style={styles.detailRow}>
          <Text style={styles.detailLabel}>{row.label}</Text>
          <Text style={styles.detailValue}>{row.value}</Text>
        </View>
      ))}
    </View>
  )
}

function pushRow(rows: { label: string; value: string }[], label: string, value: unknown) {
  const text = detailText(value).trim()
  if (!text) {
    return
  }
  rows.push({ label, value: text })
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
  filters: {
    flexDirection: 'row',
    gap: space.sm,
    paddingBottom: space.sm,
  },
  segment: {
    paddingHorizontal: space.md,
    paddingVertical: space.sm,
    borderRadius: radius.md,
    backgroundColor: colors.surfaceMuted,
    minHeight: controlSize,
    justifyContent: 'center',
  },
  segmentOn: {
    backgroundColor: colors.primarySubtle,
  },
  segmentLabel: {
    fontSize: typography.sm,
    color: colors.muted,
    fontWeight: '600',
  },
  segmentLabelOn: {
    color: colors.primary,
  },
  list: {
    paddingHorizontal: space.lg,
    paddingBottom: space['4xl'],
    gap: space.md,
  },
  card: {
    backgroundColor: colors.surface,
    borderRadius: radius.lg,
    borderWidth: 1,
    borderColor: colors.border,
    padding: space.base,
    gap: space.sm,
  },
  cardRefusal: {
    borderColor: colors.warning,
    backgroundColor: colors.accentSubtle,
  },
  rowBetween: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    gap: space.sm,
  },
  kind: {
    fontSize: typography.xs,
    fontWeight: '700',
    color: colors.primary,
    textTransform: 'uppercase',
    letterSpacing: 0.4,
  },
  date: {
    fontSize: typography.xs,
    color: colors.faint,
  },
  title: {
    fontSize: typography.lg,
    fontWeight: '700',
    color: colors.ink,
  },
  summary: {
    fontSize: typography.sm,
    color: colors.muted,
    lineHeight: 20,
  },
  meta: {
    fontSize: typography.sm,
    color: colors.faint,
  },
  hint: {
    fontSize: typography.xs,
    color: colors.faint,
    marginTop: space.xs,
  },
  details: {
    marginTop: space.sm,
    paddingTop: space.md,
    borderTopWidth: 1,
    borderTopColor: colors.border,
    gap: space.md,
  },
  detailList: {
    gap: space.md,
  },
  detailRow: {
    gap: space.xs,
  },
  detailLabel: {
    fontSize: typography.xs,
    fontWeight: '700',
    color: colors.muted,
    textTransform: 'uppercase',
    letterSpacing: 0.3,
  },
  detailValue: {
    fontSize: typography.base,
    color: colors.ink,
    lineHeight: 22,
  },
  pdfBtn: {
    alignSelf: 'flex-start',
    backgroundColor: colors.primary,
    borderRadius: radius.md,
    paddingHorizontal: space.base,
    paddingVertical: space.sm,
    minHeight: controlSize,
    justifyContent: 'center',
  },
  pdfBtnLabel: {
    color: colors.onPrimary,
    fontWeight: '700',
    fontSize: typography.sm,
  },
})
