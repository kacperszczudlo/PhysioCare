import { render, screen, fireEvent } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import { MemoryRouter } from 'react-router-dom'
import { AppLayout } from '../AppLayout'

// Mock useAuth
vi.mock('@/auth/AuthContext', () => ({
  useAuth: () => ({
    user: {
      id: 'therapist-1',
      first_name: 'Jan',
      last_name: 'Kowalski',
      email: 'jan@example.com',
      avatar_url: null,
    },
    logout: vi.fn(),
  }),
}))

// Mock useTherapistRealtimeConnection
vi.mock('@/realtime/useTherapistRealtimeConnection', () => ({
  useTherapistRealtimeConnection: vi.fn(),
}))

describe('AppLayout Component', () => {
  it('renders brand mark, product title, and main navigation links', () => {
    render(
      <MemoryRouter>
        <AppLayout />
      </MemoryRouter>,
    )

    expect(screen.getByText('PhysioCare')).toBeInTheDocument()
    expect(screen.getByText('Pulpit')).toBeInTheDocument()
    expect(screen.getByText('Harmonogram')).toBeInTheDocument()
    expect(screen.getByText('Pacjenci')).toBeInTheDocument()
    expect(screen.getByText('Ćwiczenia')).toBeInTheDocument()
    expect(screen.getByText('Profil')).toBeInTheDocument()
    expect(screen.getByText('Ustawienia')).toBeInTheDocument()
    expect(screen.getByText('Jan Kowalski')).toBeInTheDocument()
  })

  it('manages mobile drawer toggle with proper ARIA attributes', () => {
    render(
      <MemoryRouter>
        <AppLayout />
      </MemoryRouter>,
    )

    const toggle = screen.getByRole('button', { name: 'Otwórz nawigację' })
    expect(toggle).toHaveAttribute('aria-expanded', 'false')
    expect(toggle).toHaveAttribute('aria-controls', 'app-shell-drawer')

    // Kliknij toggle - otwarcie menu
    fireEvent.click(toggle)
    expect(toggle).toHaveAttribute('aria-expanded', 'true')
    expect(toggle).toHaveAttribute('aria-label', 'Zamknij nawigację')

    // Kliknij ponownie - zamknięcie
    fireEvent.click(toggle)
    expect(toggle).toHaveAttribute('aria-expanded', 'false')
  })

  it('closes mobile drawer on Escape key press', () => {
    render(
      <MemoryRouter>
        <AppLayout />
      </MemoryRouter>,
    )

    const toggle = screen.getByRole('button', { name: 'Otwórz nawigację' })
    fireEvent.click(toggle)
    expect(toggle).toHaveAttribute('aria-expanded', 'true')

    fireEvent.keyDown(window, { key: 'Escape' })
    expect(toggle).toHaveAttribute('aria-expanded', 'false')
  })

  it('closes mobile drawer when clicking a navigation link', () => {
    render(
      <MemoryRouter>
        <AppLayout />
      </MemoryRouter>,
    )

    const toggle = screen.getByRole('button', { name: 'Otwórz nawigację' })
    fireEvent.click(toggle)
    expect(toggle).toHaveAttribute('aria-expanded', 'true')

    const patientsLink = screen.getByText('Pacjenci')
    fireEvent.click(patientsLink)
    expect(toggle).toHaveAttribute('aria-expanded', 'false')
  })
})
