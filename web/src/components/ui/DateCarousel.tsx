import { useEffect, useMemo, useRef } from 'react'

import { addDays, startOfDay, toDateInputValue } from '@/lib/scheduleTime'

import './DateCarousel.css'

interface DateCarouselProps {
  /** ISO date `YYYY-MM-DD`. */
  value: string
  onChange: (next: string) => void
  label: string
  /** Inclusive lower bound as `YYYY-MM-DD`. */
  minimumDate?: string
  dayCount?: number
  id?: string
  required?: boolean
  hint?: string
}

function parseIsoDate(value: string): Date {
  const [y, m, d] = value.split('-').map(Number)
  if (!y || !m || !d) {
    return startOfDay(new Date())
  }
  return new Date(y, m - 1, d)
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

export function DateCarousel({
  value,
  onChange,
  label,
  minimumDate,
  dayCount = 90,
  id,
  required,
  hint,
}: DateCarouselProps) {
  const minDay = startOfDay(minimumDate ? parseIsoDate(minimumDate) : addDays(new Date(), -30))
  const selected = startOfDay(parseIsoDate(value || toDateInputValue(new Date())))
  const listRef = useRef<HTMLDivElement>(null)

  const days = useMemo(() => {
    return Array.from({ length: dayCount }, (_, index) => addDays(minDay, index))
  }, [minDay.getTime(), dayCount])

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
    <div className="date-carousel" id={id}>
      <span className="date-carousel__label">
        {label}
        {required ? <span className="date-carousel__required"> *</span> : null}
      </span>
      <div className="date-carousel__track" ref={listRef} role="listbox" aria-label={label}>
        {days.map((day) => {
          const iso = toDateInputValue(day)
          const selectedDay = sameDay(day, selected)
          const isToday = sameDay(day, today)
          return (
            <button
              key={iso}
              type="button"
              role="option"
              aria-selected={selectedDay}
              className={
                selectedDay ? 'date-carousel__chip date-carousel__chip--on' : 'date-carousel__chip'
              }
              onClick={() => onChange(iso)}
            >
              <span className="date-carousel__weekday">{isToday ? 'dziś' : weekdayShort(day)}</span>
              <span className="date-carousel__num">{day.getDate()}</span>
              <span className="date-carousel__month">{monthShort(day)}</span>
            </button>
          )
        })}
      </div>
      {hint ? <span className="date-carousel__hint">{hint}</span> : null}
    </div>
  )
}
