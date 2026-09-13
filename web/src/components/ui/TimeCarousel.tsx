import { useCallback, useEffect, useMemo, useRef, useState } from 'react'

import { DAY_END_HOUR, DAY_START_HOUR, SNAP_MINUTES } from '@/lib/scheduleTime'

import './TimeCarousel.css'

const ITEM_HEIGHT = 44
const SETTLE_MS = 140

interface TimeCarouselProps {
  value: string
  onChange: (next: string) => void
  label?: string
  hint?: string
  startHour?: number
  endHour?: number
  minuteStep?: number
  id?: string
  required?: boolean
}

function pad(n: number): string {
  return String(n).padStart(2, '0')
}

function parseTime(value: string): { hour: number; minute: number } {
  const [h, m] = value.split(':').map(Number)
  return {
    hour: Number.isFinite(h) ? h : DAY_START_HOUR,
    minute: Number.isFinite(m) ? m : 0,
  }
}

function snapMinute(minute: number, step: number): number {
  const snapped = Math.round(minute / step) * step
  return snapped === 60 ? 60 - step : snapped
}

function indexFromScroll(scrollTop: number, length: number): number {
  const index = Math.round(scrollTop / ITEM_HEIGHT)
  return Math.max(0, Math.min(length - 1, index))
}

interface WheelProps {
  items: string[]
  selectedIndex: number
  onChangeIndex: (index: number) => void
  ariaLabel: string
}

function ScrollWheel({ items, selectedIndex, onChangeIndex, ariaLabel }: WheelProps) {
  const ref = useRef<HTMLDivElement>(null)
  const [activeIndex, setActiveIndex] = useState(selectedIndex)
  const dragging = useRef(false)
  const moved = useRef(false)
  const ignoreScroll = useRef(false)
  const settleTimer = useRef<number | null>(null)
  const selectedIndexRef = useRef(selectedIndex)
  const onChangeIndexRef = useRef(onChangeIndex)
  const itemsLengthRef = useRef(items.length)

  selectedIndexRef.current = selectedIndex
  onChangeIndexRef.current = onChangeIndex
  itemsLengthRef.current = items.length

  function clearSettle() {
    if (settleTimer.current != null) {
      window.clearTimeout(settleTimer.current)
      settleTimer.current = null
    }
  }

  function withIgnoredScroll(action: () => void) {
    ignoreScroll.current = true
    action()
    window.requestAnimationFrame(() => {
      ignoreScroll.current = false
    })
  }

  const scrollToIndex = useCallback((index: number) => {
    const node = ref.current
    if (!node) {
      return
    }
    withIgnoredScroll(() => {
      node.scrollTop = index * ITEM_HEIGHT
    })
  }, [])

  const emitIndex = useCallback((index: number) => {
    setActiveIndex(index)
    scrollToIndex(index)
    if (index !== selectedIndexRef.current) {
      onChangeIndexRef.current(index)
    }
  }, [scrollToIndex])

  const commit = useCallback((scrollTop: number) => {
    clearSettle()
    dragging.current = false
    const next = indexFromScroll(scrollTop, itemsLengthRef.current)
    emitIndex(next)
  }, [emitIndex])

  function scheduleCommit(scrollTop: number) {
    clearSettle()
    settleTimer.current = window.setTimeout(() => commit(scrollTop), SETTLE_MS)
  }

  useEffect(() => {
    setActiveIndex(selectedIndex)
    if (dragging.current) {
      return
    }
    scrollToIndex(selectedIndex)
  }, [selectedIndex, items.length, scrollToIndex])

  useEffect(() => {
    const node = ref.current
    if (!node) {
      return
    }

    function onScrollEnd() {
      if (ignoreScroll.current || !ref.current) {
        return
      }
      commit(ref.current.scrollTop)
    }

    node.addEventListener('scrollend', onScrollEnd)
    return () => {
      node.removeEventListener('scrollend', onScrollEnd)
      clearSettle()
    }
  }, [commit])

  return (
    <div className="time-carousel__col" aria-label={`${ariaLabel}: ${items[activeIndex] ?? ''}`}>
      <div className="time-carousel__highlight" aria-hidden />
      <div
        ref={ref}
        className="time-carousel__wheel"
        role="listbox"
        aria-label={ariaLabel}
        tabIndex={0}
        onScroll={(event) => {
          if (ignoreScroll.current) {
            return
          }
          const scrollTop = event.currentTarget.scrollTop
          moved.current = true
          setActiveIndex(indexFromScroll(scrollTop, items.length))
          scheduleCommit(scrollTop)
        }}
        onPointerDown={() => {
          dragging.current = true
          moved.current = false
        }}
        onPointerUp={() => {
          dragging.current = false
        }}
        onPointerCancel={() => {
          dragging.current = false
        }}
        onKeyDown={(event) => {
          if (event.key === 'ArrowUp' || event.key === 'ArrowDown') {
            event.preventDefault()
            const delta = event.key === 'ArrowUp' ? -1 : 1
            const next = Math.max(0, Math.min(items.length - 1, activeIndex + delta))
            clearSettle()
            emitIndex(next)
          }
        }}
      >
        {items.map((item, index) => {
          const selected = index === activeIndex
          return (
            <button
              key={`${item}-${index}`}
              type="button"
              className={
                selected ? 'time-carousel__item time-carousel__item--on' : 'time-carousel__item'
              }
              role="option"
              aria-selected={selected}
              tabIndex={-1}
              onClick={(event) => {
                if (moved.current) {
                  event.preventDefault()
                  return
                }
                clearSettle()
                dragging.current = false
                emitIndex(index)
              }}
            >
              {item}
            </button>
          )
        })}
      </div>
    </div>
  )
}

export function TimeCarousel({
  value,
  onChange,
  label = 'Godzina',
  hint,
  startHour = DAY_START_HOUR,
  endHour = DAY_END_HOUR,
  minuteStep = SNAP_MINUTES,
  id,
  required,
}: TimeCarouselProps) {
  const hours = useMemo(() => {
    const list: number[] = []
    for (let hour = startHour; hour <= endHour; hour += 1) {
      list.push(hour)
    }
    return list
  }, [startHour, endHour])

  const minutes = useMemo(() => {
    const list: number[] = []
    for (let minute = 0; minute < 60; minute += minuteStep) {
      list.push(minute)
    }
    return list
  }, [minuteStep])

  const parsed = parseTime(value)
  const hour = Math.min(endHour, Math.max(startHour, parsed.hour))
  const minute = snapMinute(parsed.minute, minuteStep)
  const hourIndex = Math.max(0, hours.indexOf(hour))
  const minuteIndex = Math.max(0, minutes.indexOf(minute))

  function emit(nextHour: number, nextMinute: number) {
    onChange(`${pad(nextHour)}:${pad(nextMinute)}`)
  }

  return (
    <div className="time-carousel" id={id}>
      <span className="time-carousel__label">
        {label}
        {required ? <span className="time-carousel__required"> *</span> : null}
      </span>
      <p className="time-carousel__readout" aria-live="polite">
        {pad(hour)}:{pad(minute)}
      </p>
      <div className="time-carousel__wheels" role="group" aria-label={label}>
        <ScrollWheel
          ariaLabel="Godzina"
          items={hours.map((item) => pad(item))}
          selectedIndex={hourIndex}
          onChangeIndex={(index) => emit(hours[index] ?? startHour, minute)}
        />
        <span className="time-carousel__sep" aria-hidden>
          :
        </span>
        <ScrollWheel
          ariaLabel="Minuta"
          items={minutes.map((item) => pad(item))}
          selectedIndex={minuteIndex}
          onChangeIndex={(index) => emit(hour, minutes[index] ?? 0)}
        />
      </div>
      <span className="time-carousel__hint">{hint ?? 'Przewiń albo kliknij godzinę'}</span>
    </div>
  )
}
