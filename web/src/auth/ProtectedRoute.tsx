import { Navigate, Outlet, useLocation } from 'react-router-dom'

import { useAuth } from '@/auth/AuthContext'
import { Skeleton, SkeletonWrapper } from '@/components/ui/Skeleton'

/**
 * Strażnik tras chronionych autoryzacją w React Router.
 *
 * Przepuszcza zalogowanych fizjoterapeutów do podrzędnego widoku (`<Outlet />`),
 * wyświetla stan ładowania `Skeleton` podczas weryfikacji sesji lub przekierowuje
 * niezalogowanych użytkowników do formularza logowania (`/login`).
 */
export function ProtectedRoute() {
  const { isAuthenticated, isLoading } = useAuth()
  const location = useLocation()

  if (isLoading) {
    return (
      <SkeletonWrapper label="Ładowanie sesji…" className="app-boot">
        <div
          style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '1rem' }}
        >
          <Skeleton circle width="48px" height="48px" />
          <Skeleton width="140px" height="1.2rem" radius="sm" />
        </div>
      </SkeletonWrapper>
    )
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace state={{ from: location }} />
  }

  return <Outlet />
}

/**
 * Strażnik tras przeznaczonych dla niezalogowanych gości (np. /login, /register).
 *
 * Automatycznie przekierowuje zalogowanych użytkowników do pulpitu głównego (`/`),
 * uniemożliwiając ponowne wyświetlenie formularza logowania.
 */
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

  const isPasswordReset =
    location.pathname === '/reset' ||
    location.pathname === '/password-reset' ||
    location.pathname === '/verify-email'
  if (isAuthenticated && !isPasswordReset) {
    return <Navigate to="/" replace />
  }

  return <Outlet />
}
