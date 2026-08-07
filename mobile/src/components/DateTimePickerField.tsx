import { useEffect, useMemo, useRef, useState } from 'react'
import {
  NativeScrollEvent,
  NativeSyntheticEvent,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from 'react-native'

import { colors, radius, space, typography } from '@/theme/tokens'

const DAY_CHIP_WIDTH = 64
const DAY_CHIP_GAP = 8
const WHEEL_ITEM_HEIGHT = 44
const WHEEL_VISIBLE = 5
const WHEEL_PAD = ((WHEEL_VISIBLE - 1) / 2) * WHEEL_ITEM_HEIGHT
const DEFAULT_MINUTE_STEP = 15
const CLINIC_START_HOUR = 7
const CLINIC_END_HOUR = 20

interface DateTimePickerFieldProps {
  label: string
  value: Date
  onChange: (next: Date) => void
  hint?: string
  error?: string | null
  minimumDate?: Date
  dayCount?: number
  minuteStep?: number
  startHour?: number
  endHour?: number
}

function startOfDay(date: Date): Date {
  return new Date(date.getFullYear(), date.getMonth(), date.getDate())
}

function sameDay(a: Date, b: Date): boolean {
  return (
    a.getFullYear() === b.getFullYear() &&
    a.getMonth() === b.getMonth() &&
    a.getDate() === b.getDate()
  )
}

function clampDate(date: Date, min?: Date): Date {
  if (!min) {
    return date
  }
  return date.getTime() < min.getTime() ? new Date(min) : date
}

function buildDays(from: Date, count: number): Date[] {
  const base = startOfDay(from)
  return Array.from({ length: count }, (_, index) => {
    const day = new Date(base)
    day.setDate(base.getDate() + index)
    return day
  })
}

function buildHours(startHour: number, endHour: number): number[] {
  const hours: number[] = []
  for (let hour = startHour; hour <= endHour; hour += 1) {
    hours.push(hour)
  }
  return hours
}

function buildMinutes(step: number): number[] {
  const minutes: number[] = []
  for (let minute = 0; minute < 60; minute += step) {
    minutes.push(minute)
  }
  return minutes
}

function snapMinute(minute: number, step: number): number {
  const snapped = Math.round(minute / step) * step
  return snapped === 60 ? 60 - step : snapped
}

function weekdayShort(date: Date): string {
  return new Intl.DateTimeFormat('pl-PL', { weekday: 'short' }).format(date)
}

function dayNumber(date: Date): string {
  return String(date.getDate())
}

function monthShort(date: Date): string {
  return new Intl.DateTimeFormat('pl-PL', { month: 'short' }).format(date)
}

function formatSummary(date: Date): string {
  return new Intl.DateTimeFormat('pl-PL', {
    weekday: 'long',
    day: 'numeric',
    month: 'long',
    hour: '2-digit',
    minute: '2-digit',
  }).format(date)
}

function pad2(n: number): string {
  return String(n).padStart(2, '0')
}

function indexFromOffset(offsetY: number, length: number): number {
  const index = Math.round(offsetY / WHEEL_ITEM_HEIGHT)
  return Math.max(0, Math.min(length - 1, index))
}

interface WheelColumnProps {
  items: string[]
  selectedIndex: number
  onChangeIndex: (index: number) => void
  accessibilityLabel: string
}

function WheelColumn({ items, selectedIndex, onChangeIndex, accessibilityLabel }: WheelColumnProps) {
  const scrollRef = useRef<ScrollView>(null)
  const [activeIndex, setActiveIndex] = useState(selectedIndex)
  const isUserScrolling = useRef(false)

  useEffect(() => {
    setActiveIndex(selectedIndex)
    if (isUserScrolling.current) {
      return
    }
    const id = requestAnimationFrame(() => {
      scrollRef.current?.scrollTo({
        y: selectedIndex * WHEEL_ITEM_HEIGHT,
        animated: false,
      })
    })
    return () => cancelAnimationFrame(id)
  }, [selectedIndex, items.length])

  function syncFromOffset(offsetY: number, commit: boolean) {
    const next = indexFromOffset(offsetY, items.length)
    setActiveIndex(next)
    if (commit) {
      scrollRef.current?.scrollTo({ y: next * WHEEL_ITEM_HEIGHT, animated: true })
      if (next !== selectedIndex) {
        onChangeIndex(next)
      }
    }
  }

  function onScroll(event: NativeSyntheticEvent<NativeScrollEvent>) {
    if (!isUserScrolling.current) {
      return
    }
    syncFromOffset(event.nativeEvent.contentOffset.y, false)
  }

  function onScrollBegin() {
    isUserScrolling.current = true
  }

  function onMomentumEnd(event: NativeSyntheticEvent<NativeScrollEvent>) {
    syncFromOffset(event.nativeEvent.contentOffset.y, true)
    isUserScrolling.current = false
  }

  function onDragEnd(event: NativeSyntheticEvent<NativeScrollEvent>) {
    const velocity = event.nativeEvent.velocity?.y ?? 0
    if (Math.abs(velocity) < 0.05) {
      syncFromOffset(event.nativeEvent.contentOffset.y, true)
      isUserScrolling.current = false
    }
  }

  return (
    <View
      style={styles.wheelCol}
      accessibilityLabel={`${accessibilityLabel}: ${items[activeIndex] ?? ''}`}
      accessibilityRole="adjustable"
    >
      <View pointerEvents="none" style={styles.wheelHighlight} />
      <ScrollView
        ref={scrollRef}
        style={styles.wheelScroll}
        showsVerticalScrollIndicator={false}
        snapToInterval={WHEEL_ITEM_HEIGHT}
        snapToAlignment="start"
        disableIntervalMomentum
        decelerationRate="fast"
        nestedScrollEnabled
        scrollEventThrottle={16}
        onScroll={onScroll}
        onScrollBeginDrag={onScrollBegin}
        onMomentumScrollBegin={onScrollBegin}
        onMomentumScrollEnd={onMomentumEnd}
        onScrollEndDrag={onDragEnd}
        contentContainerStyle={styles.wheelContent}
      >
        {items.map((item, index) => {
          const selected = index === activeIndex
          const distance = Math.abs(index - activeIndex)
          return (
            <View key={`${item}-${index}`} style={styles.wheelItem}>
              <Text
                style={[
                  styles.wheelText,
                  selected ? styles.wheelTextOn : null,
                  distance === 1 ? styles.wheelTextNear : null,
                ]}
              >
                {item}
              </Text>
            </View>
          )
        })}
      </ScrollView>
      <View pointerEvents="none" style={styles.wheelFadeTop} />
      <View pointerEvents="none" style={styles.wheelFadeBottom} />
    </View>
  )
}

export function DateTimePickerField({
  label,
  value,
  onChange,
  hint,
  error,
  minimumDate,
  dayCount = 42,
  minuteStep = DEFAULT_MINUTE_STEP,
  startHour = CLINIC_START_HOUR,
  endHour = CLINIC_END_HOUR,
}: DateTimePickerFieldProps) {
  const minTime = useMemo(
    () => startOfDay(minimumDate ?? new Date()).getTime(),
    [minimumDate],
  )
  const minDay = useMemo(() => new Date(minTime), [minTime])
  const days = useMemo(() => buildDays(minDay, dayCount), [minDay, dayCount])
  const hours = useMemo(() => buildHours(startHour, endHour), [startHour, endHour])
  const minutes = useMemo(() => buildMinutes(minuteStep), [minuteStep])

  const safeValue = useMemo(() => {
    const next = clampDate(value, minDay)
    const hour = Math.min(endHour, Math.max(startHour, next.getHours()))
    const minute = snapMinute(next.getMinutes(), minuteStep)
    return new Date(next.getFullYear(), next.getMonth(), next.getDate(), hour, minute, 0, 0)
  }, [value, minDay, startHour, endHour, minuteStep])

  const dayIndex = Math.max(
    0,
    days.findIndex((day) => sameDay(day, safeValue)),
  )
  const hourIndex = Math.max(0, hours.indexOf(safeValue.getHours()))
  const minuteIndex = Math.max(0, minutes.indexOf(safeValue.getMinutes()))

  const dayScrollRef = useRef<ScrollView>(null)
  const [expanded, setExpanded] = useState(true)

  useEffect(() => {
    const timer = requestAnimationFrame(() => {
      dayScrollRef.current?.scrollTo({
        x: Math.max(0, dayIndex * (DAY_CHIP_WIDTH + DAY_CHIP_GAP) - DAY_CHIP_WIDTH),
        animated: false,
      })
    })
    return () => cancelAnimationFrame(timer)
  }, [dayIndex])

  function emit(day: Date, hour: number, minute: number) {
    onChange(new Date(day.getFullYear(), day.getMonth(), day.getDate(), hour, minute, 0, 0))
  }

  const selectedTimeLabel = `${pad2(hours[hourIndex] ?? startHour)}:${pad2(minutes[minuteIndex] ?? 0)}`

  return (
    <View style={styles.wrap}>
      <Text style={styles.label}>{label}</Text>

      <Pressable
        onPress={() => setExpanded((open) => !open)}
        style={[styles.summary, error ? styles.summaryError : null]}
        accessibilityRole="button"
        accessibilityState={{ expanded }}
        accessibilityHint="Otwiera wybór daty i godziny"
      >
        <View style={styles.summaryBody}>
          <Text style={styles.summaryValue}>{formatSummary(safeValue)}</Text>
          <Text style={styles.summaryAction}>{expanded ? 'Zwiń' : 'Zmień'}</Text>
        </View>
      </Pressable>

      {expanded ? (
        <View style={styles.panel}>
          <Text style={styles.sectionLabel}>Dzień</Text>
          <ScrollView
            ref={dayScrollRef}
            horizontal
            nestedScrollEnabled
            showsHorizontalScrollIndicator={false}
            contentContainerStyle={styles.dayRow}
            decelerationRate="fast"
            snapToInterval={DAY_CHIP_WIDTH + DAY_CHIP_GAP}
          >
            {days.map((day, index) => {
              const selected = index === dayIndex
              const isToday = sameDay(day, new Date())
              return (
                <Pressable
                  key={day.toISOString()}
                  onPress={() => emit(day, hours[hourIndex] ?? startHour, minutes[minuteIndex] ?? 0)}
                  style={[styles.dayChip, selected ? styles.dayChipOn : null]}
                  accessibilityRole="button"
                  accessibilityState={{ selected }}
                  accessibilityLabel={`${weekdayShort(day)} ${dayNumber(day)} ${monthShort(day)}`}
                >
                  <Text style={[styles.dayWeekday, selected ? styles.dayTextOn : null]}>
                    {isToday ? 'dziś' : weekdayShort(day)}
                  </Text>
                  <Text style={[styles.dayNum, selected ? styles.dayTextOn : null]}>
                    {dayNumber(day)}
                  </Text>
                  <Text style={[styles.dayMonth, selected ? styles.dayTextOn : null]}>
                    {monthShort(day)}
                  </Text>
                </Pressable>
              )
            })}
          </ScrollView>

          <Text style={styles.sectionLabel}>Godzina</Text>
          <Text style={styles.timeReadout} accessibilityLiveRegion="polite">
            {selectedTimeLabel}
          </Text>
          <View style={styles.wheels}>
            <WheelColumn
              accessibilityLabel="Godzina"
              items={hours.map((hour) => pad2(hour))}
              selectedIndex={hourIndex}
              onChangeIndex={(index) =>
                emit(days[dayIndex] ?? minDay, hours[index] ?? startHour, minutes[minuteIndex] ?? 0)
              }
            />
            <Text style={styles.wheelSeparator}>:</Text>
            <WheelColumn
              accessibilityLabel="Minuta"
              items={minutes.map((minute) => pad2(minute))}
              selectedIndex={minuteIndex}
              onChangeIndex={(index) =>
                emit(days[dayIndex] ?? minDay, hours[hourIndex] ?? startHour, minutes[index] ?? 0)
              }
            />
          </View>
          <Text style={styles.wheelHint}>Przewiń w górę lub w dół</Text>
        </View>
      ) : null}

      {error ? (
        <Text style={styles.error} accessibilityLiveRegion="polite">
          {error}
        </Text>
      ) : hint ? (
        <Text style={styles.hint}>{hint}</Text>
      ) : null}
    </View>
  )
}

const styles = StyleSheet.create({
  wrap: { gap: space.sm },
  label: {
    fontSize: typography.sm,
    fontWeight: '600',
    color: colors.ink,
  },
  summary: {
    minHeight: 52,
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: radius.md,
    paddingHorizontal: space.base,
    paddingVertical: space.md,
    backgroundColor: colors.surface,
  },
  summaryError: {
    borderColor: colors.danger,
  },
  summaryBody: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    gap: space.md,
  },
  summaryValue: {
    flex: 1,
    fontSize: typography.base,
    fontWeight: '600',
    color: colors.ink,
    textTransform: 'capitalize',
  },
  summaryAction: {
    fontSize: typography.sm,
    fontWeight: '700',
    color: colors.primary,
  },
  panel: {
    gap: space.md,
    padding: space.base,
    borderRadius: radius.lg,
    borderWidth: 1,
    borderColor: colors.border,
    backgroundColor: colors.surfaceMuted,
  },
  sectionLabel: {
    fontSize: typography.xs,
    fontWeight: '700',
    color: colors.muted,
    textTransform: 'uppercase',
    letterSpacing: 0.4,
  },
  timeReadout: {
    alignSelf: 'center',
    fontSize: typography['3xl'],
    fontWeight: '700',
    fontVariant: ['tabular-nums'],
    color: colors.ink,
    letterSpacing: 1,
    lineHeight: 36,
  },
  dayRow: {
    gap: DAY_CHIP_GAP,
    paddingVertical: space.xs,
  },
  dayChip: {
    width: DAY_CHIP_WIDTH,
    paddingVertical: space.sm,
    borderRadius: radius.md,
    borderWidth: 1,
    borderColor: colors.border,
    backgroundColor: colors.surface,
    alignItems: 'center',
    gap: 2,
  },
  dayChipOn: {
    borderColor: colors.primary,
    backgroundColor: colors.primary,
  },
  dayWeekday: {
    fontSize: typography.xs,
    color: colors.muted,
    textTransform: 'lowercase',
  },
  dayNum: {
    fontSize: typography.lg,
    fontWeight: '700',
    color: colors.ink,
  },
  dayMonth: {
    fontSize: typography.xs,
    color: colors.muted,
    textTransform: 'lowercase',
  },
  dayTextOn: {
    color: colors.onPrimary,
  },
  wheels: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: space.sm,
    height: WHEEL_ITEM_HEIGHT * WHEEL_VISIBLE,
  },
  wheelCol: {
    width: 88,
    height: WHEEL_ITEM_HEIGHT * WHEEL_VISIBLE,
    overflow: 'hidden',
    borderRadius: radius.md,
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.border,
  },
  wheelScroll: {
    zIndex: 2,
  },
  wheelContent: {
    paddingVertical: WHEEL_PAD,
  },
  wheelHighlight: {
    position: 'absolute',
    left: 4,
    right: 4,
    top: WHEEL_PAD,
    height: WHEEL_ITEM_HEIGHT,
    borderRadius: radius.sm,
    backgroundColor: colors.primarySubtle,
    borderWidth: 1,
    borderColor: colors.primary,
    zIndex: 0,
  },
  wheelFadeTop: {
    position: 'absolute',
    left: 0,
    right: 0,
    top: 0,
    height: WHEEL_PAD,
    zIndex: 3,
    backgroundColor: 'transparent',
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: colors.border,
  },
  wheelFadeBottom: {
    position: 'absolute',
    left: 0,
    right: 0,
    bottom: 0,
    height: WHEEL_PAD,
    zIndex: 3,
    backgroundColor: 'transparent',
    borderTopWidth: StyleSheet.hairlineWidth,
    borderTopColor: colors.border,
  },
  wheelItem: {
    height: WHEEL_ITEM_HEIGHT,
    alignItems: 'center',
    justifyContent: 'center',
  },
  wheelText: {
    fontSize: typography.lg,
    fontVariant: ['tabular-nums'],
    color: colors.faint,
  },
  wheelTextNear: {
    color: colors.muted,
  },
  wheelTextOn: {
    color: colors.ink,
    fontWeight: '700',
    fontSize: typography.xl,
  },
  wheelSeparator: {
    fontSize: typography['2xl'],
    fontWeight: '700',
    color: colors.ink,
    marginBottom: 2,
  },
  wheelHint: {
    textAlign: 'center',
    fontSize: typography.xs,
    color: colors.muted,
  },
  error: {
    fontSize: typography.sm,
    color: colors.danger,
  },
  hint: {
    fontSize: typography.sm,
    color: colors.muted,
  },
})
