import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach, beforeAll } from 'vitest'
import { MemoryRouter } from 'react-router-dom'
import { AdminPrivacyPage } from '../AdminPrivacyPage'
import { adminApi } from '@/api/admin'
import { ToastProvider } from '@/components/ui/ToastContext'
import type { AdminConsent, AdminPrivacyRequest, Paginated } from '@/api/types'

vi.mock('@/api/admin', () => ({
  adminApi: {
    getPrivacyRequests: vi.fn(),
    processPrivacyRequest: vi.fn(),
    getConsents: vi.fn(),
  },
}))

const mockRequests: AdminPrivacyRequest[] = [
  {
    id: 'req-uuid-1',
    user_id: 'user-uuid-1',
    user_email: 'pacjent@example.com',
    user_full_name: 'Jan Pacjent',
    reason: 'Nie korzystam już z aplikacji',
    processed_at: null,
    notes: 'email_at_request=pacjent@example.com',
    created_at: '2026-03-01T10:00:00Z',
    is_processed: false,
  },
  {
    id: 'req-uuid-2',
    user_id: 'user-uuid-2',
    user_email: 'stary@example.com',
    user_full_name: 'Usunięte Konto',
    reason: 'Wycofanie zgód',
    processed_at: '2026-03-02T12:00:00Z',
    notes: 'email_at_request=stary@example.com',
    created_at: '2026-02-28T09:00:00Z',
    is_processed: true,
  },
]

const mockConsents: AdminConsent[] = [
  {
    id: 'consent-uuid-1',
    user_id: 'user-uuid-1',
    user_email: 'pacjent@example.com',
    user_full_name: 'Jan Pacjent',
    consent_type: 'TERMS_REQUIRED',
    consent_type_display: 'Regulamin (wymagany)',
    granted: true,
    granted_at: '2026-01-15T08:00:00Z',
  },
  {
    id: 'consent-uuid-2',
    user_id: 'user-uuid-1',
    user_email: 'pacjent@example.com',
    user_full_name: 'Jan Pacjent',
    consent_type: 'MARKETING_OPTIONAL',
    consent_type_display: 'Marketing (opcjonalny)',
    granted: false,
    granted_at: '2026-01-15T08:00:00Z',
  },
]

function renderComponent() {
  return render(
    <ToastProvider>
      <MemoryRouter>
        <AdminPrivacyPage />
      </MemoryRouter>
    </ToastProvider>,
  )
}

describe('AdminPrivacyPage Component', () => {
  beforeAll(() => {
    HTMLDialogElement.prototype.showModal = vi.fn(function mockShowModal(this: HTMLDialogElement) {
      this.open = true
    })
    HTMLDialogElement.prototype.close = vi.fn(function mockClose(this: HTMLDialogElement) {
      this.open = false
    })
  })

  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(adminApi.getPrivacyRequests).mockResolvedValue({
      count: 2,
      results: mockRequests,
    } as Paginated<AdminPrivacyRequest>)
    vi.mocked(adminApi.getConsents).mockResolvedValue({
      count: 2,
      results: mockConsents,
    } as Paginated<AdminConsent>)
    vi.mocked(adminApi.processPrivacyRequest).mockResolvedValue({
      ...mockRequests[0],
      is_processed: true,
      processed_at: '2026-03-03T10:00:00Z',
    })
  })

  it('renders page header and privacy deletion requests list', async () => {
    renderComponent()

    expect(screen.getByText('RODO i Zarządzanie Prywatnością')).toBeInTheDocument()

    await waitFor(() => {
      expect(screen.getByText('Jan Pacjent')).toBeInTheDocument()
      expect(screen.getByText('pacjent@example.com')).toBeInTheDocument()
      expect(screen.getByText('Nie korzystam już z aplikacji')).toBeInTheDocument()
      expect(screen.getByText('Oczekuje na realizację')).toBeInTheDocument()
      expect(screen.getByText('Zrealizowany')).toBeInTheDocument()
    })
  })

  it('switches to consents tab and renders consents registry', async () => {
    renderComponent()

    await waitFor(() => {
      expect(screen.getByText(/Wnioski o usunięcie konta/)).toBeInTheDocument()
    })

    const consentsTab = screen.getByText(/Rejestr zgód pacjentów/)
    fireEvent.click(consentsTab)

    await waitFor(() => {
      expect(adminApi.getConsents).toHaveBeenCalled()
      expect(screen.getByText('Regulamin (wymagany)')).toBeInTheDocument()
      expect(screen.getByText('Marketing (opcjonalny)')).toBeInTheDocument()
      expect(screen.getByText('Udzielona')).toBeInTheDocument()
      expect(screen.getByText('Brak zgody')).toBeInTheDocument()
    })
  })

  it('opens confirmation modal and processes deletion request with notes', async () => {
    renderComponent()

    await waitFor(() => {
      expect(screen.getByText('Zrealizuj (RODO)')).toBeInTheDocument()
    })

    const processBtn = screen.getByText('Zrealizuj (RODO)')
    fireEvent.click(processBtn)

    expect(screen.getByText('Potwierdzenie Realizacji Wniosku RODO (Art. 17)')).toBeInTheDocument()

    const notesInput = screen.getByPlaceholderText(/Zweryfikowano telefonicznie/)
    fireEvent.change(notesInput, { target: { value: 'Potwierdzono tożsamość pacjenta' } })

    const confirmBtn = screen.getByText('Zrealizuj usunięcie (Anonimizacja)')
    fireEvent.click(confirmBtn)

    await waitFor(() => {
      expect(adminApi.processPrivacyRequest).toHaveBeenCalledWith(
        'req-uuid-1',
        'Potwierdzono tożsamość pacjenta',
      )
    })
  })

  it('renders properly styled empty state when there are no privacy deletion requests', async () => {
    vi.mocked(adminApi.getPrivacyRequests).mockResolvedValueOnce({
      count: 0,
      results: [],
    } as Paginated<AdminPrivacyRequest>)

    renderComponent()

    await waitFor(() => {
      expect(
        screen.getByText('Brak wniosków o usunięcie konta w wybranym filtrze.'),
      ).toBeInTheDocument()
      expect(screen.getByText('Wnioskodawca')).toBeInTheDocument()
      expect(screen.getByText('Powód rezygnacji')).toBeInTheDocument()
    })
  })

  it('renders properly styled empty state when there are no consent entries in registry', async () => {
    vi.mocked(adminApi.getConsents).mockResolvedValueOnce({
      count: 0,
      results: [],
    } as Paginated<AdminConsent>)

    renderComponent()

    await waitFor(() => {
      expect(screen.getByText(/Wnioski o usunięcie konta/)).toBeInTheDocument()
    })

    const consentsTab = screen.getByText(/Rejestr zgód pacjentów/)
    fireEvent.click(consentsTab)

    await waitFor(() => {
      expect(
        screen.getByText('Brak wpisów w rejestrze zgód dla wybranych filtrów.'),
      ).toBeInTheDocument()
      expect(screen.getByText('Użytkownik')).toBeInTheDocument()
      expect(screen.getByText('Typ zgody')).toBeInTheDocument()
    })
  })
})
