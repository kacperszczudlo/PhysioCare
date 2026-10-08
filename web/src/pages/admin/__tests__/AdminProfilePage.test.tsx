import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { MemoryRouter } from 'react-router-dom'
import { AdminProfilePage } from '../AdminProfilePage'
import { authApi } from '@/api/auth'
import { ToastProvider } from '@/components/ui/ToastContext'

const mockRefreshSession = vi.fn().mockResolvedValue(undefined)

const mockUser = {
  id: 'admin-uuid-1',
  first_name: 'Kacper',
  last_name: 'Administrator',
  email: 'admin@physiocare.pl',
  role: 'ADMIN' as const,
}

vi.mock('@/auth/AuthContext', () => ({
  useAuth: () => ({
    user: mockUser,
    refreshSession: mockRefreshSession,
    isAuthenticated: true,
  }),
}))

vi.mock('@/api/auth', () => ({
  authApi: {
    getMFAStatus: vi.fn(),
    updateMe: vi.fn(),
  },
}))

function renderComponent() {
  return render(
    <ToastProvider>
      <MemoryRouter>
        <AdminProfilePage />
      </MemoryRouter>
    </ToastProvider>,
  )
}

describe('AdminProfilePage Component', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(authApi.getMFAStatus).mockResolvedValue({
      is_enabled: true,
      mfa_required_for_role: false,
    })
    vi.mocked(authApi.updateMe).mockResolvedValue({
      user: {
        id: 'admin-uuid-1',
        first_name: 'Kacper Jan',
        last_name: 'Administrator',
        email: 'admin@physiocare.pl',
        role: 'ADMIN',
      },
    })
  })

  it('renders admin personal info and 2FA status', async () => {
    renderComponent()

    expect(screen.getByText('Mój profil')).toBeInTheDocument()
    expect(screen.getByDisplayValue('Kacper')).toBeInTheDocument()
    expect(screen.getByDisplayValue('Administrator')).toBeInTheDocument()
    expect(screen.getByText('admin@physiocare.pl')).toBeInTheDocument()
    expect(screen.getByText('Administrator systemu (ADMIN)')).toBeInTheDocument()

    await waitFor(() => {
      expect(screen.getByText(/2FA Aktywne/i)).toBeInTheDocument()
    })
  })

  it('submits profile changes and calls authApi.updateMe', async () => {
    renderComponent()

    const firstNameInput = screen.getByLabelText(/Imię/i)
    fireEvent.change(firstNameInput, { target: { value: 'Kacper Jan' } })

    const submitBtn = screen.getByRole('button', { name: 'Zapisz zmiany' })
    fireEvent.submit(submitBtn.closest('form')!)

    await waitFor(() => {
      expect(authApi.updateMe).toHaveBeenCalledWith({
        first_name: 'Kacper Jan',
        last_name: 'Administrator',
      })
      expect(mockRefreshSession).toHaveBeenCalled()
    })
  })
})
