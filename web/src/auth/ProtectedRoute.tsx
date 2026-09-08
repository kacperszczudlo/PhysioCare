import { Navigate, Outlet, useLocation } from 'react-router-dom'

import { useAuth } from '@/auth/AuthContext'

export function ProtectedRoute() {
  const { isAuthenticated, isLoading } = useAuth()
  const location = useLocation()

  if (isLoading) {
    return (
      <div className="app-boot" role="status" aria-live="polite">
        <span className="app-boot__pulse" aria-hidden="true" />
        <p>Ładowanie sesji…</p>
      </div>
    )
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace state={{ from: location }} />
  }

  return <Outlet />
}

export function GuestRoute() {
  const { isAuthenticated, isLoading } = useAuth()
  const location = useLocation()

  if (isLoading) {
    return (
      <div className="app-boot" role="status" aria-live="polite">
        <span className="app-boot__pulse" aria-hidden="true" />
        <p>Ładowanie sesji…</p>
      </div>
    )
  }

  const isPasswordReset = location.pathname === '/reset' || location.pathname === '/password-reset'
  if (isAuthenticated && !isPasswordReset) {
    return <Navigate to="/" replace />
  }

  return <Outlet />
}
