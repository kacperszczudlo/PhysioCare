import { Navigate, Outlet, useLocation } from 'react-router-dom'

import type { UserRole } from '@/api/types'
import { useAuth } from '@/auth/AuthContext'
import { Skeleton, SkeletonWrapper } from '@/components/ui/Skeleton'

interface RoleRouteProps {
  /** Tablica dozwolonych ról dla danej ścieżki. */
  allowedRoles?: UserRole[]
  /** Opcjonalna ścieżka przekierowania w przypadku braku uprawnień. */
  fallbackPath?: string
}

/**
 * Zaawansowany strażnik tras z weryfikacją ról (RBAC).
 *
 * Przepuszcza użytkowników, których rola znajduje się w `allowedRoles`.
 * W razie braku uprawnień przekierowuje do dedykowanego panelu danej roli:
 * - ADMIN -> /admin
 * - THERAPIST -> /
 * - PATIENT -> /patient-portal
 */
export function RoleRoute({ allowedRoles, fallbackPath }: RoleRouteProps) {
  const { user, isAuthenticated, isLoading } = useAuth()
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

  if (!isAuthenticated || !user) {
    return <Navigate to="/login" replace state={{ from: location }} />
  }

  if (allowedRoles && !allowedRoles.includes(user.role)) {
    if (fallbackPath) {
      return <Navigate to={fallbackPath} replace />
    }
    if (user.role === 'ADMIN') {
      return <Navigate to="/admin" replace />
    }
    if (user.role === 'THERAPIST') {
      return <Navigate to="/" replace />
    }
    return <Navigate to="/patient-portal" replace />
  }

  return <Outlet />
}

/**
 * Standardowy strażnik tras chronionych autoryzacją w React Router.
 */
export function ProtectedRoute() {
  return <RoleRoute />
}

/**
 * Strażnik tras przeznaczonych dla niezalogowanych gości (np. /login, /register).
 *
 * Automatycznie przekierowuje zalogowanych użytkowników do odpowiedniego pulpitu
 * w zależności od posiadanej roli (ADMIN -> /admin, THERAPIST -> /, PATIENT -> /patient-portal).
 */
export function GuestRoute() {
  const { user, isAuthenticated, isLoading } = useAuth()
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
    const dest =
      user?.role === 'ADMIN' ? '/admin' : user?.role === 'PATIENT' ? '/patient-portal' : '/'
    return <Navigate to={dest} replace />
  }

  return <Outlet />
}
