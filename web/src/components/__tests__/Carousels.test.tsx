import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import { DateCarousel } from '../ui/DateCarousel'
import { DayCarousel } from '../ui/DayCarousel'
import { TimeCarousel } from '../ui/TimeCarousel'

describe('Web Carousel Components', () => {
  describe('TimeCarousel', () => {
    it('renders label and current time readout', () => {
      const handleChange = vi.fn()
      render(<TimeCarousel value="09:15" onChange={handleChange} label="Godzina wizyty" />)

      expect(screen.getByText('Godzina wizyty')).toBeInTheDocument()
      expect(screen.getByText('09:15')).toBeInTheDocument()
    })

    it('changes time when clicking hour or minute options', () => {
      const handleChange = vi.fn()
      render(<TimeCarousel value="09:15" onChange={handleChange} label="Godzina" />)

      const hourOption = screen.getByRole('option', { name: '10' })
      fireEvent.click(hourOption)

      expect(handleChange).toHaveBeenCalledWith('10:15')
    })
  })

  describe('DayCarousel', () => {
    it('renders day chips and handles day selection', () => {
      const handleChange = vi.fn()
      const testDate = new Date(2026, 8, 15) // Sept 15, 2026
      render(<DayCarousel value={testDate} onChange={handleChange} dayCount={7} />)

      expect(screen.getByRole('listbox', { name: 'Dzień' })).toBeInTheDocument()
      const buttons = screen.getAllByRole('option')
      expect(buttons.length).toBe(7)

      // Click the second chip
      fireEvent.click(buttons[1]!)
      expect(handleChange).toHaveBeenCalledTimes(1)
    })
  })

  describe('DateCarousel', () => {
    it('renders date chips and selects date on click', () => {
      const handleChange = vi.fn()
      render(
        <DateCarousel
          value="2026-09-15"
          onChange={handleChange}
          label="Data rozpoczęcia"
          dayCount={5}
        />,
      )

      expect(screen.getByText('Data rozpoczęcia')).toBeInTheDocument()
      const buttons = screen.getAllByRole('option')
      expect(buttons.length).toBe(5)

      fireEvent.click(buttons[2]!)
      expect(handleChange).toHaveBeenCalledTimes(1)
    })
  })
})
