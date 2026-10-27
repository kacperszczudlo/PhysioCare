import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { authApi } from '@/api/auth'
import * as AuthContextModule from '@/auth/AuthContext'
import { MFAEnforcementModal } from '../MFAEnforcementModal'

vi.mock('@/api/auth', () => ({
  authApi: {
    setupMFA: vi.fn(),
    enableMFA: vi.fn(),
  },
}))

describe('MFAEnforcementModal', () => {
  const mockLogout = vi.fn().mockResolvedValue(undefined)
  const mockUpdateUser = vi.fn()

  beforeEach(() => {
    vi.clearAllMocks()
    vi.spyOn(AuthContextModule, 'useAuth').mockReturnValue({
      user: {
        id: 'u1',
        email: 'therapist@physiocare.test',
        role: 'THERAPIST',
        first_name: 'Adam',
        last_name: 'Nowak',
        has_mfa: false,
        mfa_required: true,
      },
      isLoading: false,
      isAuthenticated: true,
      login: vi.fn(),
      loginMFA: vi.fn(),
      loginWithGoogle: vi.fn(),
      register: vi.fn(),
      verifyEmail: vi.fn(),
      resendEmailCode: vi.fn(),
      logout: mockLogout,
      refreshSession: vi.fn(),
      requestPasswordReset: vi.fn(),
      verifyPasswordResetCode: vi.fn(),
      confirmPasswordReset: vi.fn(),
      updateUser: mockUpdateUser,
    })
  })

  it('does not render when user is null', () => {
    vi.spyOn(AuthContextModule, 'useAuth').mockReturnValue({
      user: null,
      isLoading: false,
      isAuthenticated: false,
      login: vi.fn(),
      loginMFA: vi.fn(),
      loginWithGoogle: vi.fn(),
      register: vi.fn(),
      verifyEmail: vi.fn(),
      resendEmailCode: vi.fn(),
      logout: mockLogout,
      refreshSession: vi.fn(),
      requestPasswordReset: vi.fn(),
      verifyPasswordResetCode: vi.fn(),
      confirmPasswordReset: vi.fn(),
      updateUser: mockUpdateUser,
    })

    const { container } = render(<MFAEnforcementModal />)
    expect(container).toBeEmptyDOMElement()
  })

  it('does not render when user has mfa_required = false (e.g. PATIENT)', () => {
    vi.spyOn(AuthContextModule, 'useAuth').mockReturnValue({
      user: {
        id: 'u2',
        email: 'patient@physiocare.test',
        role: 'PATIENT',
        first_name: 'Jan',
        last_name: 'Kowalski',
        has_mfa: false,
        mfa_required: false,
      },
      isLoading: false,
      isAuthenticated: true,
      login: vi.fn(),
      loginMFA: vi.fn(),
      loginWithGoogle: vi.fn(),
      register: vi.fn(),
      verifyEmail: vi.fn(),
      resendEmailCode: vi.fn(),
      logout: mockLogout,
      refreshSession: vi.fn(),
      requestPasswordReset: vi.fn(),
      verifyPasswordResetCode: vi.fn(),
      confirmPasswordReset: vi.fn(),
      updateUser: mockUpdateUser,
    })

    const { container } = render(<MFAEnforcementModal />)
    expect(container).toBeEmptyDOMElement()
  })

  it('does not render when user already has has_mfa = true', () => {
    vi.spyOn(AuthContextModule, 'useAuth').mockReturnValue({
      user: {
        id: 'u1',
        email: 'therapist@physiocare.test',
        role: 'THERAPIST',
        first_name: 'Adam',
        last_name: 'Nowak',
        has_mfa: true,
        mfa_required: true,
      },
      isLoading: false,
      isAuthenticated: true,
      login: vi.fn(),
      loginMFA: vi.fn(),
      loginWithGoogle: vi.fn(),
      register: vi.fn(),
      verifyEmail: vi.fn(),
      resendEmailCode: vi.fn(),
      logout: mockLogout,
      refreshSession: vi.fn(),
      requestPasswordReset: vi.fn(),
      verifyPasswordResetCode: vi.fn(),
      confirmPasswordReset: vi.fn(),
      updateUser: mockUpdateUser,
    })

    const { container } = render(<MFAEnforcementModal />)
    expect(container).toBeEmptyDOMElement()
  })

  it('automatically triggers setupMFA and displays QR and secret key', async () => {
    vi.mocked(authApi.setupMFA).mockResolvedValueOnce({
      secret_key: 'JBSWY3DPEHPK3PXP',
      otpauth_url: 'otpauth://totp/PhysioCare:therapist@test?secret=JBSWY3DPEHPK3PXP',
      qr_code_svg: '<svg><rect width="100" height="100" /></svg>',
    })

    render(<MFAEnforcementModal />)

    expect(await screen.findByText('Skonfiguruj uwierzytelnianie dwuskładnikowe (2FA)')).toBeInTheDocument()
    expect(screen.getByText('JBSWY3DPEHPK3PXP')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /aktywuj i przejdź dalej/i })).toBeInTheDocument()
  })

  it('handles full activation flow and updates user state after seeing backup codes', async () => {
    vi.mocked(authApi.setupMFA).mockResolvedValueOnce({
      secret_key: 'TESTSECRETKEY123',
      otpauth_url: 'otpauth://totp/PhysioCare',
      qr_code_svg: '<svg></svg>',
    })
    vi.mocked(authApi.enableMFA).mockResolvedValueOnce({
      message: '2FA aktywowane',
      backup_codes: ['code-1111', 'code-2222', 'code-3333'],
    })

    render(<MFAEnforcementModal />)

    await screen.findByText('TESTSECRETKEY123')
    const codeInput = screen.getByPlaceholderText('123456')

    fireEvent.change(codeInput, { target: { value: '123456' } })
    const submitBtn = screen.getByRole('button', { name: /aktywuj i przejdź dalej/i })
    fireEvent.click(submitBtn)

    await waitFor(() => {
      expect(authApi.enableMFA).toHaveBeenCalledWith('123456')
    })

    expect(await screen.findByText('Kody zapasowe')).toBeInTheDocument()
    expect(screen.getByText('code-1111')).toBeInTheDocument()
    expect(screen.getByText('code-2222')).toBeInTheDocument()

    const finishBtn = screen.getByRole('button', { name: /przejdź do systemu/i })
    fireEvent.click(finishBtn)

    expect(mockUpdateUser).toHaveBeenCalledWith({ has_mfa: true })
  })

  it('allows user to log out if they choose not to configure 2FA now', async () => {
    vi.mocked(authApi.setupMFA).mockResolvedValueOnce({
      secret_key: 'TESTSECRETKEY123',
      otpauth_url: 'otpauth://totp/PhysioCare',
      qr_code_svg: '<svg></svg>',
    })

    render(<MFAEnforcementModal />)

    const logoutBtn = await screen.findByRole('button', { name: /wyloguj się/i })
    fireEvent.click(logoutBtn)

    expect(mockLogout).toHaveBeenCalledTimes(1)
  })
})
