import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { MemoryRouter } from 'react-router-dom'
import { AdminReviewsPage } from '../AdminReviewsPage'
import { adminApi } from '@/api/admin'
import { ToastProvider } from '@/components/ui/ToastContext'
import type { AdminReview, AdminReviewListResponse } from '@/api/types'

vi.mock('@/api/admin', () => ({
  adminApi: {
    getReviews: vi.fn(),
    toggleReviewVisibility: vi.fn(),
  },
}))

const mockReviews: AdminReview[] = [
  {
    id: 'review-1',
    patient_id: 'patient-1',
    patient_name: 'Anna Kowalska',
    therapist_id: 'therapist-1',
    therapist_name: 'Jan Terapeuta',
    rating: 5,
    comment: 'Doskonała rehabilitacja, ból barku minął po 3 sesjach.',
    is_anonymous: false,
    is_visible: true,
    therapist_reply: 'Dziękuję za zaufanie!',
    therapist_replied_at: '2026-03-02T10:00:00Z',
    created_at: '2026-03-01T15:30:00Z',
  },
  {
    id: 'review-2',
    patient_id: 'patient-2',
    patient_name: 'Anonimowy Pacjent',
    therapist_id: 'therapist-1',
    therapist_name: 'Jan Terapeuta',
    rating: 1,
    comment: 'Wizyta odwołana bez uprzedzenia.',
    is_anonymous: true,
    is_visible: false,
    created_at: '2026-02-28T09:00:00Z',
  },
]

const mockResponse: AdminReviewListResponse = {
  count: 2,
  results: mockReviews,
}

function renderComponent() {
  return render(
    <ToastProvider>
      <MemoryRouter>
        <AdminReviewsPage />
      </MemoryRouter>
    </ToastProvider>,
  )
}

describe('AdminReviewsPage Component', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders reviews list with ratings, comments, and visibility badge', async () => {
    vi.mocked(adminApi.getReviews).mockResolvedValue(mockResponse)

    renderComponent()

    await waitFor(() => {
      expect(screen.getByText('Moderacja Opinii Pacjentów')).toBeInTheDocument()
    })

    expect(screen.getByText('Anna Kowalska')).toBeInTheDocument()
    expect(
      screen.getByText(/Doskonała rehabilitacja, ból barku minął po 3 sesjach./),
    ).toBeInTheDocument()
    expect(screen.getByText('Widoczna publicznie')).toBeInTheDocument()
    expect(screen.getByText('Odpowiedź fizjoterapeuty (Jan Terapeuta):')).toBeInTheDocument()

    expect(screen.getByText('Anonimowy Pacjent')).toBeInTheDocument()
    expect(screen.getByText(/Wizyta odwołana bez uprzedzenia./)).toBeInTheDocument()
    expect(screen.getByText('Ukryta (zmoderowana)')).toBeInTheDocument()
  })

  it('toggles visibility when moderation button is clicked', async () => {
    vi.mocked(adminApi.getReviews).mockResolvedValue(mockResponse)
    vi.mocked(adminApi.toggleReviewVisibility).mockResolvedValue({
      id: 'review-1',
      is_visible: false,
    })

    renderComponent()

    await waitFor(() => {
      expect(screen.getByText('Anna Kowalska')).toBeInTheDocument()
    })

    const hideBtn = screen.getByRole('button', { name: 'Ukryj opinię' })
    fireEvent.click(hideBtn)

    await waitFor(() => {
      expect(adminApi.toggleReviewVisibility).toHaveBeenCalledWith('review-1', false)
    })
  })
})
