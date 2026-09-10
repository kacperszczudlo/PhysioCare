import { useFocusEffect, useRouter } from 'expo-router'
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
import type {
  ClinicalDocumentItem,
  ClinicalDocumentKind,
  ExercisePlanItem,
  TreatmentEpisode,
} from '@/api/types'
import { EmptyState, ErrorBanner, LoadingBlock } from '@/components/AsyncState'
import { ScreenHeader } from '@/components/ScreenHeader'
import { downloadAuthenticatedMediaToCache } from '@/lib/authMedia'
import { formatDate } from '@/lib/format'
import { isDocumentRealtimeEvent, isDashboardRealtimeEvent } from '@/realtime/types'
import { useRealtimeEvents } from '@/realtime/useRealtimeEvents'
import { useSilentPoll } from '@/realtime/useSilentPoll'
import { colors, controlSize, radius, space, typography } from '@/theme/tokens'

type MainTab = 'treatment' | 'exercises' | 'documents'
type DocFilterKey = 'all' | ClinicalDocumentKind

const MAIN_TABS: { key: MainTab; label: string }[] = [
  { key: 'treatment', label: 'Leczenie' },
  { key: 'exercises', label: 'Ćwiczenia' },
  { key: 'documents', label: 'Dokumenty' },
]

const DOC_FILTERS: { key: DocFilterKey; label: string }[] = [
  { key: 'all', label: 'Wszystkie' },
  { key: 'visit_summary', label: 'Po wizycie' },
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
  const router = useRouter()
  const [mainTab, setMainTab] = useState<MainTab>('treatment')
  const [docFilter, setDocFilter] = useState<DocFilterKey>('all')
  const [episodes, setEpisodes] = useState<TreatmentEpisode[]>([])
  const [exercises, setExercises] = useState<ExercisePlanItem[]>([])
  const [docs, setDocs] = useState<ClinicalDocumentItem[]>([])
  const [expandedId, setExpandedId] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [busyId, setBusyId] = useState<string | null>(null)
  const mainTabRef = useRef(mainTab)
  const docFilterRef = useRef(docFilter)
  mainTabRef.current = mainTab
  docFilterRef.current = docFilter
  const softReloadTimer = useRef<ReturnType<typeof setTimeout> | null>(null)

  const load = useCallback(async (opts?: { silent?: boolean }) => {
    if (!opts?.silent) {
      setError(null)
    }
    try {
      const tab = mainTabRef.current
      if (tab === 'treatment') {
        setEpisodes(await patientApi.getEpisodes())
      } else if (tab === 'exercises') {
        setExercises(await patientApi.getExercises('all'))
      } else {
        const kind = docFilterRef.current === 'all' ? undefined : docFilterRef.current
        setDocs(await patientApi.getClinicalDocuments(kind))
      }
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
      void load()
    }, [load, mainTab, docFilter]),
  )

  useRealtimeEvents(
    useCallback(
      (event) => {
        const relevant =
          isDocumentRealtimeEvent(event) ||
          (mainTabRef.current === 'exercises' && isDashboardRealtimeEvent(event))
        if (!relevant) {
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

  function switchMainTab(next: MainTab) {
    if (next === mainTab) {
      return
    }
    setMainTab(next)
    setExpandedId(null)
    setLoading(true)
  }

  function switchDocFilter(next: DocFilterKey) {
    if (next === docFilter) {
      return
    }
    setDocFilter(next)
    setExpandedId(null)
    setLoading(true)
  }

  async function onToggleExercise(item: ExercisePlanItem) {
    if (busyId || !item.is_active) {
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
      setError(getErrorMessage(err, 'Nie udało się zapisać odhaczenia.'))
    } finally {
      setBusyId(null)
    }
  }

  const subtitle =
    mainTab === 'treatment'
      ? 'Twój plan leczenia — diagnoza funkcjonalna i cele terapii.'
      : mainTab === 'exercises'
        ? 'Pełny plan ćwiczeń i historia wykonania.'
        : 'Dokumenty i podsumowania wystawione przez fizjoterapeutę.'

  return (
    <View style={styles.flex}>
      <View style={styles.pad}>
        <ScreenHeader title="Dokumentacja" subtitle={subtitle} />
        <ScrollView
          horizontal
          showsHorizontalScrollIndicator={false}
          contentContainerStyle={styles.filters}
        >
          {MAIN_TABS.map((item) => (
            <Segment
              key={item.key}
              label={item.label}
              active={mainTab === item.key}
              onPress={() => switchMainTab(item.key)}
            />
          ))}
        </ScrollView>
        {mainTab === 'documents' ? (
          <ScrollView
            horizontal
            showsHorizontalScrollIndicator={false}
            contentContainerStyle={styles.filters}
          >
            {DOC_FILTERS.map((item) => (
              <Segment
                key={item.key}
                label={item.label}
                active={docFilter === item.key}
                onPress={() => switchDocFilter(item.key)}
              />
            ))}
          </ScrollView>
        ) : null}
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
                void load()
              }}
              tintColor={colors.primary}
            />
          }
        >
          {error ? <ErrorBanner message={error} onRetry={() => void load()} /> : null}

          {mainTab === 'treatment' ? (
            episodes.length === 0 ? (
              <EmptyState
                title="Brak epizodu leczenia"
                description="Gdy fizjoterapeuta rozpocznie epizod, zobaczysz tu cele terapii i podsumowanie."
              />
            ) : (
              episodes.map((episode) => (
                <EpisodeCard key={episode.id} episode={episode} />
              ))
            )
          ) : null}

          {mainTab === 'exercises' ? (
            exercises.length === 0 ? (
              <EmptyState
                title="Brak zaleceń"
                description="Przypisane ćwiczenia pojawią się tutaj wraz z historią odhaczeń."
              />
            ) : (
              exercises.map((item) => (
                <ExercisePlanCard
                  key={item.id}
                  item={item}
                  busy={busyId === item.id}
                  onToggle={() => void onToggleExercise(item)}
                  onOpen={() => router.push(`/exercise/${item.id}`)}
                />
              ))
            )
          ) : null}

          {mainTab === 'documents' ? (
            docs.length === 0 ? (
              <EmptyState
                title="Brak dokumentów"
                description="Podsumowania wizyt, kierowania, wyroby, Recepta na Ruch i PDF pojawią się tutaj."
              />
            ) : (
              docs.map((doc) => {
                const open = expandedId === `${doc.kind}:${doc.id}`
                return (
                  <DocumentCard
                    key={`${doc.kind}:${doc.id}`}
                    doc={doc}
                    expanded={open}
                    onToggle={() => setExpandedId(open ? null : `${doc.kind}:${doc.id}`)}
                    onOpenVisit={
                      doc.kind === 'visit_summary'
                        ? () => router.push(`/visit/${doc.id}`)
                        : undefined
                    }
                  />
                )
              })
            )
          ) : null}
        </ScrollView>
      )}
    </View>
  )
}

function EpisodeCard({ episode }: { episode: TreatmentEpisode }) {
  return (
    <View style={styles.card}>
      <View style={styles.rowBetween}>
        <Text style={styles.kind}>{episode.status_label}</Text>
        <Text style={styles.date}>{formatDate(episode.started_at)}</Text>
      </View>
      {episode.icd10_code ? (
        <Text style={styles.meta}>Kod roboczy ICD-10: {episode.icd10_code}</Text>
      ) : null}
      {episode.functional_diagnosis ? (
        <>
          <Text style={styles.detailLabel}>Nad czym pracujemy</Text>
          <Text style={styles.body}>{episode.functional_diagnosis}</Text>
        </>
      ) : null}
      {episode.summary_note ? (
        <>
          <Text style={styles.detailLabel}>Podsumowanie</Text>
          <Text style={styles.body}>{episode.summary_note}</Text>
        </>
      ) : null}
      {!episode.functional_diagnosis && !episode.summary_note ? (
        <Text style={styles.summary}>Epizod w trakcie — szczegóły uzupełni terapeuta.</Text>
      ) : null}
      {episode.ended_at ? (
        <Text style={styles.meta}>Zakończony: {formatDate(episode.ended_at)}</Text>
      ) : null}
    </View>
  )
}

function ExercisePlanCard({
  item,
  busy,
  onToggle,
  onOpen,
}: {
  item: ExercisePlanItem
  busy: boolean
  onToggle: () => void
  onOpen: () => void
}) {
  const doneCount = item.completions.filter((c) => c.done).length
  return (
    <Pressable
      onPress={onOpen}
      style={styles.card}
      accessibilityRole="button"
      accessibilityLabel={item.exercise_title}
    >
      <View style={styles.rowBetween}>
        <Text style={styles.kind}>{item.is_active ? 'Aktywne' : 'Zakończone'}</Text>
        <Text style={styles.date}>
          {formatDate(item.start_date)} – {formatDate(item.end_date)}
        </Text>
      </View>
      <Text style={styles.title}>{item.exercise_title}</Text>
      <Text style={styles.summary}>{item.dosage || 'Bez dawki'}</Text>
      <Text style={styles.meta}>
        Odhaczenia: {doneCount}
        {item.is_active ? (item.completed_today ? ' · dziś zrobione' : ' · dziś do zrobienia') : ''}
      </Text>
      {item.is_active ? (
        <Pressable
          onPress={(e) => {
            e.stopPropagation?.()
            onToggle()
          }}
          disabled={busy}
          style={[styles.pdfBtn, item.completed_today ? styles.toggleDone : null]}
          accessibilityRole="button"
          accessibilityLabel={item.completed_today ? 'Cofnij odhaczenie' : 'Oznacz jako zrobione'}
        >
          <Text style={styles.pdfBtnLabel}>
            {item.completed_today ? 'Cofnij dzisiejsze' : 'Oznacz na dziś'}
          </Text>
        </Pressable>
      ) : null}
    </Pressable>
  )
}

function DocumentCard({
  doc,
  expanded,
  onToggle,
  onOpenVisit,
}: {
  doc: ClinicalDocumentItem
  expanded: boolean
  onToggle: () => void
  onOpenVisit?: () => void
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
          {doc.kind === 'visit_summary' && onOpenVisit ? (
            <Pressable
              onPress={onOpenVisit}
              style={styles.pdfBtn}
              accessibilityRole="link"
              accessibilityLabel="Otwórz wizytę"
            >
              <Text style={styles.pdfBtnLabel}>Zobacz wizytę</Text>
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
  } else if (doc.kind === 'visit_summary') {
    pushRow(rows, 'Podsumowanie', d.patient_summary)
    pushRow(rows, 'Typ wizyty', d.therapy_type_name)
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
  body: {
    fontSize: typography.base,
    color: colors.ink,
    lineHeight: 22,
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
    marginTop: space.xs,
  },
  toggleDone: {
    backgroundColor: colors.muted,
  },
  pdfBtnLabel: {
    color: colors.onPrimary,
    fontWeight: '700',
    fontSize: typography.sm,
  },
})
