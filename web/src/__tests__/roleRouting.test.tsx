import { render, screen } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { RoleRoute, GuestRoute } from '@/auth/ProtectedRoute'
import type { UserRole } from '@/api/types'

let mockAuthState = {
  user: null as { id: string; email: string; role: UserRole } | null,
  isAuthenticated: false,
  isLoading: false,
}

vi.mock('@/auth/AuthContext', () => ({
  useAuth: () => mockAuthState,
}))

describe('RoleRoute RBAC Guard', () => {
  it('renders loading state when session is loading', () => {
    mockAuthState = { user: null, isAuthenticated: false, isLoading: true }

    render(
      <MemoryRouter initialEntries={['/admin']}>
        <Routes>
          <Route element={<RoleRoute allowedRoles={['ADMIN']} />}>
            <Route path="/admin" element={<div>Admin Content</div>} />
          </Route>
        </Routes>
      </MemoryRouter>,
    )

    expect(screen.getByRole('status', { name: 'Ładowanie sesji…' })).toBeInTheDocument()
  })

  it('redirects to /login if user is unauthenticated', () => {
    mockAuthState = { user: null, isAuthenticated: false, isLoading: false }

    render(
      <MemoryRouter initialEntries={['/admin']}>
        <Routes>
          <Route path="/login" element={<div>Login Page</div>} />
          <Route element={<RoleRoute allowedRoles={['ADMIN']} />}>
            <Route path="/admin" element={<div>Admin Content</div>} />
          </Route>
        </Routes>
      </MemoryRouter>,
    )

    expect(screen.getByText('Login Page')).toBeInTheDocument()
  })

  it('renders outlet when user has the allowed role', () => {
    mockAuthState = {
      user: { id: 'admin-1', email: 'admin@physiocare.pl', role: 'ADMIN' },
      isAuthenticated: true,
      isLoading: false,
    }

    render(
      <MemoryRouter initialEntries={['/admin']}>
        <Routes>
          <Route element={<RoleRoute allowedRoles={['ADMIN']} />}>
            <Route path="/admin" element={<div>Admin Protected Content</div>} />
          </Route>
        </Routes>
      </MemoryRouter>,
    )

    expect(screen.getByText('Admin Protected Content')).toBeInTheDocument()
  })

  it('redirects therapist to / when trying to access admin route', () => {
    mockAuthState = {
      user: { id: 'therapist-1', email: 'doc@physiocare.pl', role: 'THERAPIST' },
      isAuthenticated: true,
      isLoading: false,
    }

    render(
      <MemoryRouter initialEntries={['/admin']}>
        <Routes>
          <Route path="/" element={<div>Therapist Dashboard</div>} />
          <Route element={<RoleRoute allowedRoles={['ADMIN']} />}>
            <Route path="/admin" element={<div>Admin Content</div>} />
          </Route>
        </Routes>
      </MemoryRouter>,
    )

    expect(screen.getByText('Therapist Dashboard')).toBeInTheDocument()
  })

  it('redirects patient to /patient-portal when trying to access admin or clinical route', () => {
    mockAuthState = {
      user: { id: 'patient-1', email: 'patient@example.com', role: 'PATIENT' },
      isAuthenticated: true,
      isLoading: false,
    }

    render(
      <MemoryRouter initialEntries={['/admin']}>
        <Routes>
          <Route path="/patient-portal" element={<div>Patient Portal Notice</div>} />
          <Route element={<RoleRoute allowedRoles={['ADMIN']} />}>
            <Route path="/admin" element={<div>Admin Content</div>} />
          </Route>
        </Routes>
      </MemoryRouter>,
    )

    expect(screen.getByText('Patient Portal Notice')).toBeInTheDocument()
  })
})

describe('GuestRoute Guard', () => {
  it('redirects authenticated ADMIN from login to /admin', () => {
    mockAuthState = {
      user: { id: 'admin-1', email: 'admin@physiocare.pl', role: 'ADMIN' },
      isAuthenticated: true,
      isLoading: false,
    }

    render(
      <MemoryRouter initialEntries={['/login']}>
        <Routes>
          <Route path="/admin" element={<div>Admin Dashboard</div>} />
          <Route element={<GuestRoute />}>
            <Route path="/login" element={<div>Login Form</div>} />
          </Route>
        </Routes>
      </MemoryRouter>,
    )

    expect(screen.getByText('Admin Dashboard')).toBeInTheDocument()
  })

  it('redirects authenticated THERAPIST from login to /', () => {
    mockAuthState = {
      user: { id: 'therapist-1', email: 'doc@physiocare.pl', role: 'THERAPIST' },
      isAuthenticated: true,
      isLoading: false,
    }

    render(
      <MemoryRouter initialEntries={['/login']}>
        <Routes>
          <Route path="/" element={<div>Therapist Main Dashboard</div>} />
          <Route element={<GuestRoute />}>
            <Route path="/login" element={<div>Login Form</div>} />
          </Route>
        </Routes>
      </MemoryRouter>,
    )

    expect(screen.getByText('Therapist Main Dashboard')).toBeInTheDocument()
  })

  it('redirects authenticated PATIENT from login to /patient-portal', () => {
    mockAuthState = {
      user: { id: 'patient-1', email: 'patient@example.com', role: 'PATIENT' },
      isAuthenticated: true,
      isLoading: false,
    }

    render(
      <MemoryRouter initialEntries={['/login']}>
        <Routes>
          <Route path="/patient-portal" element={<div>Patient Web Notice</div>} />
          <Route element={<GuestRoute />}>
            <Route path="/login" element={<div>Login Form</div>} />
          </Route>
        </Routes>
      </MemoryRouter>,
    )

    expect(screen.getByText('Patient Web Notice')).toBeInTheDocument()
  })
})
