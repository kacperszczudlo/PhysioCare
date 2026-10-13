import { render, screen, within } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { LegalLayout } from '../LegalLayout'

const mockAuth = {
  isAuthenticated: false,
  user: null as { id: string; email: string; first_name: string; last_name: string; role: 'ADMIN' | 'THERAPIST' | 'PATIENT' } | null,
}

vi.mock('@/auth/AuthContext', () => ({
  useAuth: () => mockAuth,
  useOptionalAuth: () => mockAuth,
}))

describe('LegalLayout Component', () => {
  beforeEach(() => {
    mockAuth.isAuthenticated = false
    mockAuth.user = null
  })

  it('renders header brand, active nav items and login action when not logged in', () => {
    render(
      <MemoryRouter initialEntries={['/privacy']}>
        <Routes>
          <Route element={<LegalLayout />}>
            <Route path="/privacy" element={<div>Treść polityki prywatności</div>} />
          </Route>
        </Routes>
      </MemoryRouter>,
    )

    const headerNav = screen.getByRole('navigation', { name: 'Dokumenty prawne' })
    expect(within(headerNav).getByRole('link', { name: 'Prywatność' })).toHaveClass(
      'legal-layout__nav-link--active',
    )
    expect(within(headerNav).getByRole('link', { name: 'Cookies' })).toBeInTheDocument()
    expect(within(headerNav).getByRole('link', { name: 'Usuwanie konta' })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Zaloguj się' })).toHaveAttribute('href', '/login')
    expect(screen.getByText('Treść polityki prywatności')).toBeInTheDocument()
  })

  it('renders admin dashboard action button when user is logged in as admin', () => {
    mockAuth.isAuthenticated = true
    mockAuth.user = {
      id: 'admin-1',
      email: 'admin@physiocare.pl',
      first_name: 'Kacper',
      last_name: 'Szczudło',
      role: 'ADMIN',
    }

    render(
      <MemoryRouter initialEntries={['/privacy']}>
        <Routes>
          <Route element={<LegalLayout />}>
            <Route path="/privacy" element={<div>Treść polityki prywatności</div>} />
          </Route>
        </Routes>
      </MemoryRouter>,
    )

    const adminBtn = screen.getByRole('link', { name: 'Panel administratora' })
    expect(adminBtn).toBeInTheDocument()
    expect(adminBtn).toHaveAttribute('href', '/admin')
  })

  it('renders footer with copyright and legal navigation links', () => {
    render(
      <MemoryRouter initialEntries={['/account-deletion']}>
        <Routes>
          <Route element={<LegalLayout />}>
            <Route path="/account-deletion" element={<div>Treść usuwania konta</div>} />
          </Route>
        </Routes>
      </MemoryRouter>,
    )

    expect(screen.getByText(/PhysioCare\. Wszelkie prawa zastrzeżone\./)).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Polityka prywatności' })).toHaveAttribute('href', '/privacy')
    expect(screen.getByRole('link', { name: 'Polityka cookies' })).toHaveAttribute('href', '/cookies')
  })
})
