import { render, screen, waitFor } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { MemoryRouter } from 'react-router-dom'
import { AdminSchedulesPage } from '../AdminSchedulesPage'
import { adminApi } from '@/api/admin'
import { ToastProvider } from '@/components/ui/ToastContext'
import type { AdminSchedulingOverview } from '@/api/types'

vi.mock('@/api/admin', () => ({
  adminApi: {
    getSchedulingOverview: vi.fn(),
  },
}))

const mockOverview: AdminSchedulingOverview = {
  range: {
    start_at: '2026-03-01T00:00:00Z',
    end_at: '2026-03-08T23:59:59Z',
  },
  therapists: [
    {
      id: 'therapist-1',
      user_id: 'user-1',
      name: 'Tomasz Nowak',
      email: 'tomasz@physiocare.pl',
      qualification_level: 'Specjalista',
      rating_avg: 4.9,
      rating_count: 10,
    },
  ],
  visits: [
    {
      id: 'visit-1',
      patient_id: 'patient-1',
      patient_name: 'Michał Wiśniewski',
      therapist_id: 'therapist-1',
      therapist_name: 'Tomasz Nowak',
      therapy_type_name: 'Rehabilitacja kręgosłupa',
      therapy_type_color: '#3b82f6',
      start_at: '2026-03-02T10:00:00Z',
      end_at: '2026-03-02T11:00:00Z',
      status: 'SCHEDULED',
      location_address: 'Gabinet 102',
    },
  ],
  availability_slots: [
    {
      id: 'slot-1',
      therapist_id: 'therapist-1',
      therapist_name: 'Tomasz Nowak',
      day_of_week: 1,
      start_time: '08:00:00',
      end_time: '16:00:00',
      is_active: true,
    },
  ],
}

function renderComponent() {
  return render(
    <ToastProvider>
      <MemoryRouter>
        <AdminSchedulesPage />
      </MemoryRouter>
    </ToastProvider>,
  )
}

describe('AdminSchedulesPage Component', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders scheduling overview with visits and status badges', async () => {
    vi.mocked(adminApi.getSchedulingOverview).mockResolvedValue(mockOverview)

    renderComponent()

    await waitFor(() => {
      expect(screen.getByText('Harmonogramy & Kalendarz Kliniki')).toBeInTheDocument()
    })

    expect(screen.getByText(/Michał Wiśniewski/)).toBeInTheDocument()
    expect(screen.getByText(/Rehabilitacja kręgosłupa/)).toBeInTheDocument()
    expect(screen.getByText('Zaplanowana')).toBeInTheDocument()
    expect(screen.getByText(/Gabinet 102/)).toBeInTheDocument()
  })
})
