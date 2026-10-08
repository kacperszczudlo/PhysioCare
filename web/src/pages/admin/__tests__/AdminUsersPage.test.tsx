import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach, beforeAll } from 'vitest'
import { MemoryRouter } from 'react-router-dom'
import { AdminUsersPage } from '../AdminUsersPage'
import { adminApi } from '@/api/admin'
import { ToastProvider } from '@/components/ui/ToastContext'
import type { AdminUserListItem, AdminUserListResponse } from '@/api/types'

function renderComponent() {
  return render(
    <ToastProvider>
      <MemoryRouter>
        <AdminUsersPage />
      </MemoryRouter>
    </ToastProvider>,
  )
}

vi.mock('@/api/admin', () => ({
  adminApi: {
    getUsers: vi.fn(),
    getUserDetail: vi.fn(),
    toggleUserStatus: vi.fn(),
    resetUserPassword: vi.fn(),
    softDeleteUser: vi.fn(),
  },
}))

const mockUsers: AdminUserListItem[] = [
  {
    id: 'user-patient-1',
    first_name: 'Piotr',
    last_name: 'Zieliński',
    email: 'piotr@example.com',
    role: 'PATIENT',
    is_active: true,
    email_verified: true,
    created_at: '2026-03-01T10:00:00Z',
  },
  {
    id: 'user-therapist-1',
    first_name: 'Marek',
    last_name: 'Fizjoterapeuta',
    email: 'marek@physiocare.pl',
    role: 'THERAPIST',
    is_active: false,
    email_verified: true,
    created_at: '2026-02-15T12:00:00Z',
  },
]

const mockResponse: AdminUserListResponse = {
  count: 2,
  results: mockUsers,
}

describe('AdminUsersPage Component', () => {
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
  })

  it('renders table with fetched users and role badges', async () => {
    vi.mocked(adminApi.getUsers).mockResolvedValue(mockResponse)

    renderComponent()

    await waitFor(() => {
      expect(screen.getByText('Zarządzanie Użytkownikami')).toBeInTheDocument()
    })

    expect(screen.getByText('Piotr Zieliński')).toBeInTheDocument()
    expect(screen.getByText('piotr@example.com')).toBeInTheDocument()
    expect(screen.getByText('Pacjent (App)')).toBeInTheDocument()
    expect(screen.getByText('Aktywny')).toBeInTheDocument()

    expect(screen.getByText('Marek Fizjoterapeuta')).toBeInTheDocument()
    expect(screen.getByText('marek@physiocare.pl')).toBeInTheDocument()
    expect(screen.getByText('Fizjoterapeuta (Web)')).toBeInTheDocument()
    expect(screen.getByText('Zablokowany')).toBeInTheDocument()
  })

  it('toggles user status when block/unblock button is clicked', async () => {
    vi.mocked(adminApi.getUsers).mockResolvedValue(mockResponse)
    vi.mocked(adminApi.toggleUserStatus).mockResolvedValue({
      id: 'user-patient-1',
      is_active: false,
    })

    renderComponent()

    await waitFor(() => {
      expect(screen.getByText('Piotr Zieliński')).toBeInTheDocument()
    })

    const blockBtn = screen.getByTitle('Zablokuj konto')
    fireEvent.click(blockBtn)

    await waitFor(() => {
      expect(adminApi.toggleUserStatus).toHaveBeenCalledWith('user-patient-1', false)
    })
  })

  it('opens user detail, triggers password reset and calls resetUserPassword upon confirmation', async () => {
    vi.mocked(adminApi.getUsers).mockResolvedValue(mockResponse)
    vi.mocked(adminApi.getUserDetail).mockResolvedValue({
      id: 'user-patient-1',
      first_name: 'Piotr',
      last_name: 'Zieliński',
      email: 'piotr@example.com',
      role: 'PATIENT',
      is_active: true,
      email_verified: true,
      has_mfa: false,
      created_at: '2026-03-01T10:00:00Z',
      visits_count: 3,
    })
    vi.mocked(adminApi.resetUserPassword).mockResolvedValue({
      detail: 'Kod resetowania hasła został wysłany.',
    })

    renderComponent()

    await waitFor(() => {
      expect(screen.getByText('Piotr Zieliński')).toBeInTheDocument()
    })

    const detailButtons = screen.getAllByTitle('Szczegóły konta')
    fireEvent.click(detailButtons[0])

    await waitFor(() => {
      expect(screen.getByText('Szczegóły Użytkownika')).toBeInTheDocument()
    })

    const resetBtn = screen.getByRole('button', { name: /Wyślij reset hasła/i })
    fireEvent.click(resetBtn)

    expect(screen.getByText('Potwierdzenie wysłania resetu hasła')).toBeInTheDocument()
    const confirmBtn = screen.getByRole('button', { name: 'Wyślij kod resetu' })
    fireEvent.click(confirmBtn)

    await waitFor(() => {
      expect(adminApi.resetUserPassword).toHaveBeenCalledWith('user-patient-1')
    })
  })

  it('opens confirmation modal and performs soft delete on delete button click', async () => {
    vi.mocked(adminApi.getUsers).mockResolvedValue(mockResponse)
    vi.mocked(adminApi.softDeleteUser).mockResolvedValue({
      detail: 'Konto użytkownika zostało pomyślnie zanonimizowane i dezaktywowane (RODO).',
    })

    renderComponent()

    await waitFor(() => {
      expect(screen.getByText('Piotr Zieliński')).toBeInTheDocument()
    })

    const deleteButtons = screen.getAllByTitle('Usuń / zanonimizuj (RODO)')
    fireEvent.click(deleteButtons[0])

    // Sprawdź czy pojawił się modal z ostrzeżeniem RODO
    expect(screen.getByText('Potwierdzenie Dezaktywacji Konta (RODO)')).toBeInTheDocument()
    const confirmBtn = screen.getByRole('button', { name: 'Potwierdź dezaktywację' })
    fireEvent.click(confirmBtn)

    await waitFor(() => {
      expect(adminApi.softDeleteUser).toHaveBeenCalledWith('user-patient-1')
    })
  })

  it('opens password reset confirmation modal when quick action key icon in table row is clicked', async () => {
    vi.mocked(adminApi.getUsers).mockResolvedValue(mockResponse)
    vi.mocked(adminApi.resetUserPassword).mockResolvedValue({
      detail: 'Kod resetowania hasła został wysłany.',
    })

    renderComponent()

    await waitFor(() => {
      expect(screen.getByText('Piotr Zieliński')).toBeInTheDocument()
    })

    const quickResetBtn = screen.getAllByTitle('Wyślij kod resetu hasła')[0]
    fireEvent.click(quickResetBtn)

    expect(screen.getByText('Potwierdzenie wysłania resetu hasła')).toBeInTheDocument()
    const confirmBtn = screen.getByRole('button', { name: 'Wyślij kod resetu' })
    fireEvent.click(confirmBtn)

    await waitFor(() => {
      expect(adminApi.resetUserPassword).toHaveBeenCalledWith('user-patient-1')
    })
  })
})
