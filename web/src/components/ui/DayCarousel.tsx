import { useEffect, useMemo, useRef } from 'react'

import { addDays, startOfDay, toDateInputValue } from '@/lib/scheduleTime'

import './DayCarousel.css'

interface DayCarouselProps {
  value: Date
  onChange: (day: Date) => void
  minimumDate?: Date
  dayCount?: number
  label?: string
  id?: string
}

function sameDay(a: Date, b: Date): boolean {
  return (
    a.getFullYear() === b.getFullYear() &&
    a.getMonth() === b.getMonth() &&
    a.getDate() === b.getDate()
  )
}

function weekdayShort(date: Date): string {
  return new Intl.DateTimeFormat('pl-PL', { weekday: 'short' }).format(date)
}

function monthShort(date: Date): string {
  return new Intl.DateTimeFormat('pl-PL', { month: 'short' }).format(date)
}

export function DayCarousel({
  value,
  onChange,
  minimumDate,
  dayCount = 42,
  label = 'Dzień',
  id,
}: DayCarouselProps) {
  const minTime = useMemo(
    () => startOfDay(minimumDate ?? new Date()).getTime(),
    [minimumDate?.getTime()],
  )
  const minDay = useMemo(() => new Date(minTime), [minTime])
  const selected = startOfDay(value)
  const listRef = useRef<HTMLDivElement>(null)

  const days = useMemo(() => {
    return Array.from({ length: dayCount }, (_, index) => addDays(minDay, index))
  }, [minDay, dayCount])

  const selectedIndex = Math.max(
    0,
    days.findIndex((day) => sameDay(day, selected)),
  )

  useEffect(() => {
    const root = listRef.current
    if (!root) {
      return
    }
    const chip = root.children[selectedIndex] as HTMLElement | undefined
    chip?.scrollIntoView({ inline: 'center', block: 'nearest', behavior: 'smooth' })
  }, [selectedIndex])

  const today = startOfDay(new Date())

  return (
    <div className="day-carousel" id={id}>
      <span className="day-carousel__label">{label}</span>
      <div className="day-carousel__track" ref={listRef} role="listbox" aria-label={label}>
        {days.map((day) => {
          const selectedDay = sameDay(day, selected)
          const isToday = sameDay(day, today)
          return (
            <button
              key={toDateInputValue(day)}
              type="button"
              role="option"
              aria-selected={selectedDay}
              className={
                selectedDay ? 'day-carousel__chip day-carousel__chip--on' : 'day-carousel__chip'
              }
              onClick={() => onChange(startOfDay(day))}
            >
              <span className="day-carousel__weekday">{isToday ? 'dziś' : weekdayShort(day)}</span>
              <span className="day-carousel__num">{day.getDate()}</span>
              <span className="day-carousel__month">{monthShort(day)}</span>
            </button>
          )
        })}
      </div>
    </div>
  )
}
