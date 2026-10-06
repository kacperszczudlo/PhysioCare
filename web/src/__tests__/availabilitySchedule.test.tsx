import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { AvailabilityTabView } from '../pages/schedule/AvailabilityTabView'
import { ToastProvider } from '../components/ui/ToastContext'
import { schedulingApi } from '../api/scheduling'
import type { AvailabilitySlot } from '../api/types'

vi.mock('../api/scheduling', () => ({
  schedulingApi: {
    listAvailabilities: vi.fn(),
    listPolishHolidays: vi.fn(),
    createAvailability: vi.fn(),
    deleteAvailability: vi.fn(),
  },
}))

describe('AvailabilityTabView Component', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(schedulingApi.listPolishHolidays).mockResolvedValue([])
  })

  it('renders unconfigured state and banner when no recurring availability exists in database', async () => {
    vi.mocked(schedulingApi.listAvailabilities).mockResolvedValue([])

    render(
      <ToastProvider>
        <AvailabilityTabView />
      </ToastProvider>,
    )

    await waitFor(() => {
      expect(screen.getByText('Wymaga ustalenia i zapisu')).toBeInTheDocument()
    })

    expect(screen.getByText('Harmonogram pracy nie został jeszcze zapisany')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Zapisz i aktywuj grafik' })).toBeInTheDocument()
  })

  it('renders active state when recurring availability exists in database', async () => {
    const mockSlots: AvailabilitySlot[] = [
      {
        id: 'slot-1',
        is_recurring: true,
        day_of_week: 0,
        start_time: '08:00:00',
        end_time: '16:00:00',
        is_active: true,
      },
    ]
    vi.mocked(schedulingApi.listAvailabilities).mockResolvedValue(mockSlots)

    render(
      <ToastProvider>
        <AvailabilityTabView />
      </ToastProvider>,
    )

    await waitFor(() => {
      expect(screen.getByText('Grafik aktywny')).toBeInTheDocument()
    })

    expect(
      screen.queryByText('Harmonogram pracy nie został jeszcze zapisany'),
    ).not.toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Zapisano' })).toBeDisabled()
  })

  it('marks state as dirty with "Niezapisane zmiany" when editing days and enables save button', async () => {
    const mockSlots: AvailabilitySlot[] = [
      {
        id: 'slot-1',
        is_recurring: true,
        day_of_week: 0,
        start_time: '08:00:00',
        end_time: '16:00:00',
        is_active: true,
      },
    ]
    vi.mocked(schedulingApi.listAvailabilities).mockResolvedValue(mockSlots)

    render(
      <ToastProvider>
        <AvailabilityTabView />
      </ToastProvider>,
    )

    await waitFor(() => {
      expect(screen.getByText('Grafik aktywny')).toBeInTheDocument()
    })

    const clearBtn = screen.getByRole('button', { name: 'Wyczyść dni' })
    fireEvent.click(clearBtn)

    expect(screen.getByText('Niezapisane zmiany')).toBeInTheDocument()
    const saveBtn = screen.getByRole('button', { name: 'Zapisz zmiany' })
    expect(saveBtn).not.toBeDisabled()
  })

  it('saves schedule and calls onScheduleSaved callback', async () => {
    vi.mocked(schedulingApi.listAvailabilities).mockResolvedValueOnce([])
    vi.mocked(schedulingApi.createAvailability).mockResolvedValue({} as AvailabilitySlot)

    const onScheduleSaved = vi.fn()

    render(
      <ToastProvider>
        <AvailabilityTabView onScheduleSaved={onScheduleSaved} />
      </ToastProvider>,
    )

    await waitFor(() => {
      expect(screen.getByRole('button', { name: 'Zapisz i aktywuj grafik' })).toBeInTheDocument()
    })

    // Mock subsequent listAvailabilities after save
    vi.mocked(schedulingApi.listAvailabilities).mockResolvedValue([
      {
        id: 'slot-saved',
        is_recurring: true,
        day_of_week: 0,
        start_time: '08:00:00',
        end_time: '16:00:00',
        is_active: true,
      },
    ])

    const saveBtn = screen.getByRole('button', { name: 'Zapisz i aktywuj grafik' })
    fireEvent.click(saveBtn)

    await waitFor(() => {
      expect(schedulingApi.createAvailability).toHaveBeenCalled()
      expect(onScheduleSaved).toHaveBeenCalledTimes(1)
    })
  })
})
