import { render, screen, fireEvent } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import { MemoryRouter } from 'react-router-dom'
import { AdminLayout } from '../AdminLayout'

const mockLogout = vi.fn()

vi.mock('@/auth/AuthContext', () => ({
  useAuth: () => ({
    user: {
      id: 'admin-1',
      first_name: 'Aleksandra',
      last_name: 'Nowak',
      email: 'admin@physiocare.pl',
      role: 'ADMIN',
    },
    logout: mockLogout,
    isAuthenticated: true,
  }),
}))

describe('AdminLayout Component', () => {
  it('renders brand mark, panel title, and admin navigation links', () => {
    render(
      <MemoryRouter>
        <AdminLayout />
      </MemoryRouter>,
    )

    expect(screen.getByText('PhysioCare')).toBeInTheDocument()
    expect(screen.getByText('Panel administratora')).toBeInTheDocument()
    expect(screen.getByText('Pulpit')).toBeInTheDocument()
    expect(screen.getByText('Użytkownicy')).toBeInTheDocument()
    expect(screen.getByText('Harmonogramy')).toBeInTheDocument()
    expect(screen.getByText('Zespół fizjoterapeutów')).toBeInTheDocument()
    expect(screen.getByText('Moderacja opinii')).toBeInTheDocument()
    expect(screen.getByText('Mój profil')).toBeInTheDocument()
    expect(screen.getByText('Ustawienia')).toBeInTheDocument()
    expect(screen.getByText('Aleksandra Nowak')).toBeInTheDocument()
    expect(screen.getByText('Administrator')).toBeInTheDocument()
  })

  it('renders interactive identity link leading to /admin/profile', () => {
    render(
      <MemoryRouter>
        <AdminLayout />
      </MemoryRouter>,
    )

    const profileLink = screen.getByTitle('Przejdź do profilu administratora')
    expect(profileLink).toBeInTheDocument()
    expect(profileLink).toHaveAttribute('href', '/admin/profile')
  })

  it('toggles mobile drawer on menu toggle button click', () => {
    render(
      <MemoryRouter>
        <AdminLayout />
      </MemoryRouter>,
    )

    const toggleBtn = screen.getByRole('button', { name: 'Otwórz nawigację' })
    expect(toggleBtn).toBeInTheDocument()

    // Otwarcie menu
    fireEvent.click(toggleBtn)
    const drawer = document.querySelector('#admin-shell-drawer')
    expect(drawer?.className).toContain('app-shell__drawer--open')

    // Zamknięcie przez kliknięcie w backdrop
    const backdrop = document.querySelector('.app-shell__backdrop')
    expect(backdrop).toBeInTheDocument()
    if (backdrop) {
      fireEvent.click(backdrop)
    }
    expect(drawer?.className).not.toContain('app-shell__drawer--open')
  })
})
