import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { MemoryRouter } from 'react-router-dom'
import { PatientNoticePage } from '../pages/PatientNoticePage'

const mockLogout = vi.fn().mockResolvedValue(undefined)
const mockToast = vi.fn()

const mockUser = {
  id: 'patient-123',
  email: 'kacper.szczudlo@gmail.com',
  first_name: 'Kacper',
  last_name: 'Szczudło',
  role: 'PATIENT' as const,
}

vi.mock('@/auth/AuthContext', () => ({
  useAuth: () => ({
    user: mockUser,
    logout: mockLogout,
    isAuthenticated: true,
    isLoading: false,
  }),
}))

vi.mock('@/components/ui/ToastContext', () => ({
  useToast: () => ({
    toast: mockToast,
  }),
}))

describe('PatientNoticePage Component', () => {
  const originalEnv = import.meta.env.VITE_EXPO_MOBILE_BUILD_URL

  beforeEach(() => {
    vi.clearAllMocks()
    import.meta.env.VITE_EXPO_MOBILE_BUILD_URL = 'https://expo.dev/accounts/demo/projects/test/builds/12345'
    Object.assign(navigator, {
      clipboard: {
        writeText: vi.fn().mockResolvedValue(undefined),
      },
    })
  })

  afterEach(() => {
    import.meta.env.VITE_EXPO_MOBILE_BUILD_URL = originalEnv
  })

  it('renders patient welcome greeting and email', () => {
    render(
      <MemoryRouter>
        <PatientNoticePage />
      </MemoryRouter>,
    )

    expect(screen.getByRole('heading', { name: /Witaj, Kacper!/i })).toBeInTheDocument()
    expect(screen.getAllByText('kacper.szczudlo@gmail.com').length).toBeGreaterThanOrEqual(1)
    expect(screen.getByText('Pacjent')).toBeInTheDocument()
  })

  it('renders QR code and direct APK download link when VITE_EXPO_MOBILE_BUILD_URL is set', () => {
    render(
      <MemoryRouter>
        <PatientNoticePage />
      </MemoryRouter>,
    )

    expect(screen.getByTitle('Kod QR do pobrania aplikacji mobilnej PhysioCare')).toBeInTheDocument()

    const downloadLink = screen.getByRole('link', { name: /Pobierz aplikację \(Expo \/ APK\)/i })
    expect(downloadLink).toBeInTheDocument()
    expect(downloadLink).toHaveAttribute(
      'href',
      'https://expo.dev/accounts/demo/projects/test/builds/12345',
    )
  })

  it('renders fallback state when VITE_EXPO_MOBILE_BUILD_URL is not set', () => {
    import.meta.env.VITE_EXPO_MOBILE_BUILD_URL = ''

    render(
      <MemoryRouter>
        <PatientNoticePage />
      </MemoryRouter>,
    )

    expect(screen.getByText('Wydanie mobilne w przygotowaniu')).toBeInTheDocument()
    expect(screen.queryByTitle('Kod QR do pobrania aplikacji mobilnej PhysioCare')).not.toBeInTheDocument()
  })

  it('copies download link to clipboard on button click and shows toast', async () => {
    render(
      <MemoryRouter>
        <PatientNoticePage />
      </MemoryRouter>,
    )

    const copyBtn = screen.getByRole('button', { name: /Kopiuj link instalacyjny do schowka/i })
    fireEvent.click(copyBtn)

    await waitFor(() => {
      expect(navigator.clipboard.writeText).toHaveBeenCalledWith(
        'https://expo.dev/accounts/demo/projects/test/builds/12345',
      )
      expect(mockToast).toHaveBeenCalledWith(
        expect.objectContaining({
          type: 'success',
          message: expect.stringContaining('Skopiowano link'),
        }),
      )
    })
  })

  it('calls logout when clicking logout button', () => {
    render(
      <MemoryRouter>
        <PatientNoticePage />
      </MemoryRouter>,
    )

    const logoutBtn = screen.getByRole('button', { name: /Wyloguj się/i })
    fireEvent.click(logoutBtn)

    expect(mockLogout).toHaveBeenCalledTimes(1)
  })
})
