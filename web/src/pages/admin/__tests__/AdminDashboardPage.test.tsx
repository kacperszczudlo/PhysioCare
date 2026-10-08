import { render, screen, waitFor } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { MemoryRouter } from 'react-router-dom'
import { AdminDashboardPage } from '../AdminDashboardPage'
import { adminApi } from '@/api/admin'
import type { AdminDashboardStats } from '@/api/types'

vi.mock('@/api/admin', () => ({
  adminApi: {
    getDashboardStats: vi.fn(),
  },
}))

const mockStats: AdminDashboardStats = {
  users: {
    total: 142,
    patients_count: 120,
    therapists_count: 20,
    admins_count: 2,
    active_count: 139,
    inactive_count: 3,
    new_last_30_days: 15,
  },
  visits: {
    total: 350,
    scheduled: 45,
    completed: 280,
    cancelled: 15,
    no_show: 10,
    pending_approval: 0,
    show_up_rate_percent: 92.5,
  },
  quality: {
    rating_avg: 4.88,
    rating_count: 75,
  },
  exercises: {
    total_exercises: 84,
    total_assignments: 210,
  },
}

describe('AdminDashboardPage Component', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders loading state initially', () => {
    vi.mocked(adminApi.getDashboardStats).mockReturnValue(new Promise(() => {}))

    render(
      <MemoryRouter>
        <AdminDashboardPage />
      </MemoryRouter>,
    )

    expect(screen.getByText('Ładowanie wskaźników analitycznych…')).toBeInTheDocument()
  })

  it('loads and renders dashboard KPI cards with metrics', async () => {
    vi.mocked(adminApi.getDashboardStats).mockResolvedValue(mockStats)

    render(
      <MemoryRouter>
        <AdminDashboardPage />
      </MemoryRouter>,
    )

    await waitFor(() => {
      expect(screen.getByText('Pulpit Administracyjny')).toBeInTheDocument()
    })

    // Użytkownicy
    expect(screen.getByText('142')).toBeInTheDocument()
    expect(screen.getByText('120')).toBeInTheDocument()
    expect(screen.getByText('20')).toBeInTheDocument()
    expect(screen.getByText('+15 nowych w ost. 30 dniach')).toBeInTheDocument()

    // Wizyty
    expect(screen.getByText('350')).toBeInTheDocument()
    expect(screen.getByText('280')).toBeInTheDocument()
    expect(screen.getByText('Frekwencja: 92.5%')).toBeInTheDocument()

    // Jakość
    expect(screen.getByText('4.88')).toBeInTheDocument()
    expect(screen.getByText('75')).toBeInTheDocument()
    expect(screen.getByText('Bardzo wysokie')).toBeInTheDocument()

    // Baza ćwiczeń
    expect(screen.getAllByText('84').length).toBeGreaterThanOrEqual(1)
    expect(screen.getAllByText('210').length).toBeGreaterThanOrEqual(1)
  })

  it('renders error state when API call fails', async () => {
    vi.mocked(adminApi.getDashboardStats).mockRejectedValue(new Error('Network error'))

    render(
      <MemoryRouter>
        <AdminDashboardPage />
      </MemoryRouter>,
    )

    await waitFor(() => {
      expect(
        screen.getByText('Nie udało się pobrać statystyk systemu. Spróbuj ponownie.'),
      ).toBeInTheDocument()
    })

    expect(screen.getByRole('button', { name: 'Spróbuj ponownie' })).toBeInTheDocument()
  })
})
