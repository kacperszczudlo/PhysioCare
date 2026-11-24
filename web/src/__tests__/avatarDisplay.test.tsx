import { render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

const { mockUseAuthenticatedMediaUrl, mockPatientsList } = vi.hoisted(() => ({
  mockUseAuthenticatedMediaUrl: vi.fn(),
  mockPatientsList: vi.fn(),
}))

vi.mock('@/lib/authMedia', () => ({
  useAuthenticatedMediaUrl: mockUseAuthenticatedMediaUrl,
}))

vi.mock('@/api/treatment', () => ({
  patientsApi: {
    getPaginated: mockPatientsList,
  },
}))

describe('Web Avatar Display', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('AuthMediaImg renders authenticated image when URL resolves', async () => {
    mockUseAuthenticatedMediaUrl.mockReturnValue({
      url: 'blob:http://localhost/avatar-123',
      loading: false,
      error: false,
    })

    const { AuthMediaImg } = await import('@/components/AuthMedia')
    const { container } = render(
      <AuthMediaImg path="/media/avatars/patient.jpg" className="dash-visit__avatar" />,
    )

    const img = container.querySelector('img.dash-visit__avatar')
    expect(img).not.toBeNull()
    expect(img).toHaveAttribute('src', 'blob:http://localhost/avatar-123')
  })

  it('AuthMediaImg returns null when URL is not available', async () => {
    mockUseAuthenticatedMediaUrl.mockReturnValue({
      url: null,
      loading: false,
      error: true,
    })

    const { AuthMediaImg } = await import('@/components/AuthMedia')
    const { container } = render(
      <AuthMediaImg path="/media/avatars/missing.jpg" className="dash-visit__avatar" />,
    )

    expect(container.querySelector('img')).toBeNull()
  })

  it('PatientsPage renders avatar image for patients with avatar_url and initials fallback otherwise', async () => {
    mockUseAuthenticatedMediaUrl.mockImplementation((path: string | null | undefined) => ({
      url: path ? `blob:http://localhost${path}` : null,
      loading: false,
      error: false,
    }))
    mockPatientsList.mockResolvedValueOnce({
      count: 2,
      results: [
        {
          id: 'pat-1',
          first_name: 'Anna',
          last_name: 'Nowak',
          email: 'anna@example.com',
          phone: '500100200',
          avatar_url: '/media/avatars/anna.jpg',
        },
        {
          id: 'pat-2',
          first_name: 'Piotr',
          last_name: 'Zieliński',
          email: 'piotr@example.com',
          phone: '',
          avatar_url: '',
        },
      ],
    })

    const { PatientsPage } = await import('@/pages/PatientsPage')
    const { container } = render(
      <MemoryRouter>
        <PatientsPage />
      </MemoryRouter>,
    )

    await waitFor(() => {
      expect(screen.getByText('Anna Nowak')).toBeInTheDocument()
      expect(screen.getByText('Piotr Zieliński')).toBeInTheDocument()
    })

    const img = container.querySelector('img.patients-row__avatar')
    expect(img).not.toBeNull()
    expect(img).toHaveAttribute('src', 'blob:http://localhost/media/avatars/anna.jpg')
    expect(screen.getByText('PZ')).toBeInTheDocument()
  })
})
