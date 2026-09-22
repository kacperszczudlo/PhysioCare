/**
 * @file ProgressOverview.tsx
 * @description Podsumowanie postępów pacjenta w wykonywaniu zaleceń (wskaźnik dzisiejszy, kafelki wizyt oraz słupkowy wykres z 7 dni).
 */

import { useEffect, useState } from 'react'
import { AccessibilityInfo, Animated, StyleSheet, Text, View, type ViewProps } from 'react-native'

import type { DayProgress } from '@/lib/patientProgress'
import { colors, motion, radius, space, typography } from '@/theme/tokens'

/** Właściwości komponentu {@link ProgressOverview}. */
interface ProgressOverviewProps extends ViewProps {
  /** Liczba wykonanych dzisiaj zaleceń. */
  todayDone: number
  /** Całkowita liczba zaleceń na dzisiaj. */
  todayTotal: number
  /** Postęp w poszczególnych dniach tygodnia. */
  weekDays: DayProgress[]
  /** Liczba zrealizowanych wizyt. */
  completedVisits: number
  /** Liczba zaplanowanych nadchodzących wizyt. */
  upcomingVisits: number
}

function useReduceMotion(): boolean {
  const [reduceMotion, setReduceMotion] = useState(false)

  useEffect(() => {
    let mounted = true
    void AccessibilityInfo.isReduceMotionEnabled().then((enabled) => {
      if (mounted) {
        setReduceMotion(enabled)
      }
    })
    const sub = AccessibilityInfo.addEventListener('reduceMotionChanged', setReduceMotion)
    return () => {
      mounted = false
      sub.remove()
    }
  }, [])

  return reduceMotion
}

function useAnimatedRatio(ratio: number, reduceMotion: boolean) {
  const [anim] = useState(() => new Animated.Value(0))
  const clamped = Math.max(0, Math.min(1, ratio))

  useEffect(() => {
    if (reduceMotion) {
      anim.setValue(clamped)
      return
    }
    Animated.timing(anim, {
      toValue: clamped,
      duration: motion.large,
      useNativeDriver: false,
    }).start()
  }, [anim, clamped, reduceMotion])

  return anim
}

function TodayMeter({
  done,
  total,
  reduceMotion,
}: {
  done: number
  total: number
  reduceMotion: boolean
}) {
  const ratio = total > 0 ? done / total : 0
  const anim = useAnimatedRatio(ratio, reduceMotion)
  const width = anim.interpolate({
    inputRange: [0, 1],
    outputRange: ['0%', '100%'],
  })
  const label = total > 0 ? `Zalecenia na dziś: ${done} z ${total}` : 'Brak zaleceń na dziś'

  return (
    <View
      style={styles.meter}
      accessibilityRole="progressbar"
      accessibilityValue={{
        min: 0,
        max: Math.max(total, 1),
        now: done,
        text: label,
      }}
    >
      <View style={styles.meterHeader}>
        <Text style={styles.meterPct}>{total > 0 ? `${Math.round(ratio * 100)}%` : '—'}</Text>
        <View style={styles.meterCopy}>
          <Text style={styles.meterTitle}>
            {total > 0 ? `${done} z ${total} zaleceń` : 'Brak zaleceń na dziś'}
          </Text>
          <Text style={styles.meterHint}>
            {total === 0
              ? 'Gdy terapeuta przypisze plan, zobaczysz go tutaj.'
              : done === total
                ? 'Plan na dziś domknięty.'
                : 'Odznaczaj wykonane ćwiczenia poniżej.'}
          </Text>
        </View>
      </View>
      <View style={styles.track}>
        <Animated.View style={[styles.trackFill, { width }]} />
      </View>
    </View>
  )
}

function WeekBar({ day, reduceMotion }: { day: DayProgress; reduceMotion: boolean }) {
  const target = day.total > 0 ? Math.max(0.14, day.ratio) : 0
  const anim = useAnimatedRatio(target, reduceMotion)
  const height = anim.interpolate({
    inputRange: [0, 1],
    outputRange: [4, 56],
  })
  const empty = day.total === 0
  const a11y = empty
    ? `${day.label}: brak zaleceń`
    : `${day.label}: ${day.done} z ${day.total} zaleceń`

  return (
    <View style={styles.barCol} accessibilityLabel={a11y}>
      <View style={styles.barTrack}>
        <Animated.View
          style={[
            styles.barFill,
            day.isToday ? styles.barFillToday : null,
            empty ? styles.barEmpty : null,
            { height },
          ]}
        />
      </View>
      <Text style={[styles.barLabel, day.isToday ? styles.barLabelToday : null]}>{day.label}</Text>
    </View>
  )
}

/**
 * Widok podsumowujący postępy pacjenta (dzisiejszy pasek postępu, liczniki wizyt oraz podgląd ostatnich 7 dni).
 *
 * @param props Właściwości podsumowania postępów.
 * @returns Element React Native prezentujący statystyki i wykres.
 */
export function ProgressOverview({
  todayDone,
  todayTotal,
  weekDays,
  completedVisits,
  upcomingVisits,
  style,
  ...rest
}: ProgressOverviewProps) {
  const reduceMotion = useReduceMotion()
  const weekDone = weekDays.reduce((sum, d) => sum + d.done, 0)
  const weekTotal = weekDays.reduce((sum, d) => sum + d.total, 0)

  return (
    <View style={[styles.wrap, style]} {...rest}>
      <Text style={styles.sectionLabel}>Twój postęp</Text>
      <View style={styles.card}>
        <TodayMeter done={todayDone} total={todayTotal} reduceMotion={reduceMotion} />

        <View style={styles.chips}>
          <View style={styles.chip} accessibilityLabel={`${completedVisits} wizyt za tobą`}>
            <Text style={styles.chipValue}>{completedVisits}</Text>
            <Text style={styles.chipLabel}>wizyt za tobą</Text>
          </View>
          <View
            style={[styles.chip, styles.chipAccent]}
            accessibilityLabel={`${upcomingVisits} wizyt przed tobą`}
          >
            <Text style={[styles.chipValue, styles.chipValueAccent]}>{upcomingVisits}</Text>
            <Text style={[styles.chipLabel, styles.chipLabelAccent]}>przed tobą</Text>
          </View>
        </View>

        <View style={styles.weekBlock}>
          <View style={styles.weekHeader}>
            <Text style={styles.weekTitle}>Ostatnie 7 dni</Text>
            <Text style={styles.weekMeta}>{weekTotal > 0 ? `${weekDone}/${weekTotal}` : '—'}</Text>
          </View>
          {weekTotal === 0 ? (
            <Text style={styles.weekEmpty}>
              Tu pojawią się słupki realizacji zaleceń z tygodnia.
            </Text>
          ) : (
            <View style={styles.weekRow}>
              {weekDays.map((day) => (
                <WeekBar key={day.date} day={day} reduceMotion={reduceMotion} />
              ))}
            </View>
          )}
        </View>
      </View>
    </View>
  )
}

const styles = StyleSheet.create({
  wrap: { gap: space.sm },
  sectionLabel: {
    fontSize: typography.sm,
    fontWeight: '700',
    color: colors.muted,
    textTransform: 'uppercase',
    letterSpacing: 0.4,
  },
  card: {
    backgroundColor: colors.surface,
    borderRadius: radius.lg,
    borderWidth: 1,
    borderColor: colors.border,
    padding: space.base,
    gap: space.base,
  },
  meter: { gap: space.md },
  meterHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: space.base,
  },
  meterPct: {
    minWidth: 72,
    fontSize: typography['3xl'],
    fontWeight: '700',
    color: colors.primary,
    letterSpacing: -0.5,
  },
  meterCopy: { flex: 1, gap: 2 },
  meterTitle: {
    fontSize: typography.base,
    fontWeight: '700',
    color: colors.ink,
  },
  meterHint: {
    fontSize: typography.sm,
    color: colors.muted,
    lineHeight: 20,
  },
  track: {
    height: 10,
    borderRadius: radius.sm,
    backgroundColor: colors.primarySubtle,
    overflow: 'hidden',
  },
  trackFill: {
    height: '100%',
    borderRadius: radius.sm,
    backgroundColor: colors.primary,
  },
  chips: {
    flexDirection: 'row',
    gap: space.sm,
  },
  chip: {
    flex: 1,
    backgroundColor: colors.surfaceMuted,
    borderRadius: radius.md,
    paddingHorizontal: space.md,
    paddingVertical: space.md,
    gap: 2,
  },
  chipAccent: {
    backgroundColor: colors.primarySubtle,
  },
  chipValue: {
    fontSize: typography.xl,
    fontWeight: '700',
    color: colors.ink,
  },
  chipValueAccent: {
    color: colors.primary,
  },
  chipLabel: {
    fontSize: typography.xs,
    color: colors.muted,
    fontWeight: '600',
  },
  chipLabelAccent: {
    color: colors.primary,
  },
  weekBlock: {
    gap: space.md,
    borderTopWidth: 1,
    borderTopColor: colors.border,
    paddingTop: space.base,
  },
  weekHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  weekTitle: {
    fontSize: typography.sm,
    fontWeight: '700',
    color: colors.ink,
  },
  weekMeta: {
    fontSize: typography.sm,
    fontWeight: '700',
    color: colors.primary,
  },
  weekEmpty: {
    fontSize: typography.sm,
    color: colors.muted,
    lineHeight: 20,
  },
  weekRow: {
    flexDirection: 'row',
    alignItems: 'flex-end',
    justifyContent: 'space-between',
    gap: space.xs,
    minHeight: 80,
  },
  barCol: {
    flex: 1,
    alignItems: 'center',
    gap: space.sm,
  },
  barTrack: {
    height: 56,
    width: '100%',
    maxWidth: 28,
    justifyContent: 'flex-end',
    alignItems: 'center',
  },
  barFill: {
    width: '70%',
    minWidth: 10,
    borderRadius: radius.sm,
    backgroundColor: colors.primary,
  },
  barFillToday: {
    backgroundColor: colors.success,
  },
  barEmpty: {
    backgroundColor: colors.border,
    opacity: 0.75,
  },
  barLabel: {
    fontSize: typography.xs,
    color: colors.muted,
    fontWeight: '600',
    textTransform: 'lowercase',
  },
  barLabelToday: {
    color: colors.success,
    fontWeight: '700',
  },
})
