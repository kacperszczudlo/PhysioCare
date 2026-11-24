import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

const { mockPost, mockLogin, mockLoginMFA, mockLoginWithGoogle } = vi.hoisted(() => ({
  mockPost: vi.fn(),
  mockLogin: vi.fn(),
  mockLoginMFA: vi.fn(),
  mockLoginWithGoogle: vi.fn(),
}))

vi.mock('@/api/client', async () => {
  const actual = await vi.importActual<typeof import('@/api/client')>('@/api/client')
  return {
    ...actual,
    api: {
      ...actual.api,
      post: mockPost,
    },
  }
})

vi.mock('@/auth/AuthContext', () => ({
  useAuth: () => ({
    login: mockLogin,
    loginMFA: mockLoginMFA,
    loginWithGoogle: mockLoginWithGoogle,
  }),
}))

vi.mock('@/auth/googleRegistrationDraft', () => ({
  parseGoogleIdTokenClaims: () => ({}),
  setGoogleRegistrationDraft: vi.fn(),
}))

vi.mock('@/components/GoogleSignInButton', () => ({
  isWebGoogleSignInConfigured: () => true,
  GoogleSignInButton: ({ onCredential }: { onCredential: (token: string) => void }) => (
    <button type="button" onClick={() => onCredential('google-id-token-123')}>
      Kontynuuj z Google
    </button>
  ),
}))

vi.mock('@/hooks/useRecaptcha', () => ({
  useRecaptcha: () => ({
    isEnabled: false,
    executeRecaptcha: vi.fn().mockResolvedValue(undefined),
  }),
}))

vi.mock('@/components/ui/ToastContext', () => ({
  useToast: () => ({
    info: vi.fn(),
    error: vi.fn(),
    success: vi.fn(),
  }),
}))

describe('Google Sign-In MFA flow', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('authApi.loginWithGoogle returns mfa_required when backend requests 2FA', async () => {
    mockPost.mockResolvedValueOnce({
      mfa_required: true,
      mfa_token: 'mfa-preauth-token',
      email: 'therapist@example.com',
    })

    const { authApi } = await import('@/api/auth')
    const result = await authApi.loginWithGoogle('google-id-token')

    expect(result).toEqual({
      kind: 'mfa_required',
      mfa_token: 'mfa-preauth-token',
      email: 'therapist@example.com',
    })
  })

  it('authApi.loginWithGoogle returns authenticated when backend returns user', async () => {
    const user = {
      id: 'u-1',
      email: 'therapist@example.com',
      role: 'THERAPIST',
      first_name: 'Jan',
      last_name: 'Kowalski',
    }
    mockPost.mockResolvedValueOnce({ user })

    const { authApi } = await import('@/api/auth')
    const result = await authApi.loginWithGoogle('google-id-token')

    expect(result).toEqual({
      kind: 'authenticated',
      user,
    })
  })

  it('authApi.loginWithGoogle returns mfa_setup_required on AUTH_MFA_SETUP_REQUIRED error', async () => {
    const { ApiError } = await import('@/api/client')
    mockPost.mockRejectedValueOnce(
      new ApiError(403, 'MFA required', {
        code: 'AUTH_MFA_SETUP_REQUIRED',
        details: {
          mfa_setup_token: 'setup-tok-1',
          email: 'therapist@example.com',
        },
      }),
    )

    const { authApi } = await import('@/api/auth')
    const result = await authApi.loginWithGoogle('google-id-token')

    expect(result).toEqual({
      kind: 'mfa_setup_required',
      mfa_setup_token: 'setup-tok-1',
      email: 'therapist@example.com',
    })
  })

  it('LoginPage shows 2FA verification step after Google Sign-In when MFA is required', async () => {
    mockLoginWithGoogle.mockResolvedValueOnce({
      kind: 'mfa_required',
      mfa_token: 'mfa-preauth-token',
      email: 'therapist@example.com',
    })
    mockLoginMFA.mockResolvedValueOnce(undefined)

    const { LoginPage } = await import('@/pages/LoginPage')

    render(
      <MemoryRouter>
        <LoginPage />
      </MemoryRouter>,
    )

    fireEvent.click(screen.getByRole('button', { name: 'Kontynuuj z Google' }))

    await waitFor(() => {
      expect(screen.getByText('Weryfikacja dwuskładnikowa (2FA)')).toBeInTheDocument()
      expect(
        screen.getByText(
          'Konto therapist@example.com wymaga potwierdzenia kodem z aplikacji Google Authenticator.',
        ),
      ).toBeInTheDocument()
    })

    const input = screen.getByLabelText(/Kod z aplikacji weryfikującej/i)
    fireEvent.change(input, { target: { value: '123456' } })
    fireEvent.click(screen.getByRole('button', { name: 'Zaloguj się kodem 2FA' }))

    await waitFor(() => {
      expect(mockLoginMFA).toHaveBeenCalledWith('mfa-preauth-token', '123456')
    })
  })
})
