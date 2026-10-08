import { render, screen, waitFor } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { MemoryRouter } from 'react-router-dom'
import { AdminTherapistsPage } from '../AdminTherapistsPage'
import { adminApi } from '@/api/admin'
import { ToastProvider } from '@/components/ui/ToastContext'
import type { AdminTherapistStats } from '@/api/types'

vi.mock('@/api/admin', () => ({
  adminApi: {
    getTherapistStats: vi.fn(),
  },
}))

const mockTherapists: AdminTherapistStats[] = [
  {
    therapist_id: 'therapist-1',
    user_id: 'user-1',
    first_name: 'Tomasz',
    last_name: 'Fizjoterapeuta',
    email: 'tomasz@physiocare.pl',
    pwzf_number: '123456',
    qualification_level: 'Magister Fizjoterapii',
    experience_years: 8,
    rating_avg: 4.95,
    rating_count: 42,
    total_visits: 120,
    completed_visits: 110,
    cancelled_visits: 7,
    no_show_visits: 3,
    pending_visits: 0,
  },
]

function renderComponent() {
  return render(
    <ToastProvider>
      <MemoryRouter>
        <AdminTherapistsPage />
      </MemoryRouter>
    </ToastProvider>,
  )
}

describe('AdminTherapistsPage Component', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders therapist cards with PWZF, qualifications, visits, and ratings', async () => {
    vi.mocked(adminApi.getTherapistStats).mockResolvedValue(mockTherapists)

    renderComponent()

    await waitFor(() => {
      expect(screen.getByText('Zespół Fizjoterapeutów')).toBeInTheDocument()
    })

    expect(screen.getByText('Tomasz Fizjoterapeuta')).toBeInTheDocument()
    expect(screen.getByText('tomasz@physiocare.pl')).toBeInTheDocument()
    expect(screen.getByText('123456')).toBeInTheDocument()
    expect(screen.getByText('Magister Fizjoterapii')).toBeInTheDocument()
    expect(screen.getByText('8 lat')).toBeInTheDocument()
    expect(screen.getByText('4.95')).toBeInTheDocument()
    expect(screen.getByText('42 opinii')).toBeInTheDocument()
    expect(screen.getByText('110')).toBeInTheDocument()
    expect(screen.getByText('7')).toBeInTheDocument()
    expect(screen.getByText('3')).toBeInTheDocument()
  })
})
