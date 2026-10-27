import { useEffect, useState } from 'react'
import { Link, NavLink, Outlet, useLocation } from 'react-router-dom'

import { useAuth } from '@/auth/AuthContext'
import { AuthMediaImg } from '@/components/AuthMedia'
import { MFAEnforcementModal } from '@/components/MFAEnforcementModal'
import { useTherapistRealtimeConnection } from '@/realtime/useTherapistRealtimeConnection'
import './AppLayout.css'

const NAV: ReadonlyArray<{ to: string; label: string; end?: boolean }> = [
  { to: '/', label: 'Pulpit', end: true },
  { to: '/schedule', label: 'Harmonogram' },
  { to: '/patients', label: 'Pacjenci' },
  { to: '/exercises', label: 'Ćwiczenia' },
  { to: '/profile', label: 'Profil' },
  { to: '/settings', label: 'Ustawienia' },
]

function initials(first?: string, last?: string): string {
  const value = `${first?.charAt(0) ?? ''}${last?.charAt(0) ?? ''}`.toUpperCase()
  return value || '?'
}

/**
 * Główny szablon ramowy (Layout Shell) aplikacji webowej PhysioCare dla zalogowanych fizjoterapeutów.
 *
 * Zawiera boczny pasek nawigacji (Sidebar na desktopie, responsywny TopBar z szufladą Drawer na mobile),
 * nagłówek profilu, połączenie w czasie rzeczywistym SSE oraz kontener podrzędnych widoków tras (`<Outlet />`).
 */
export function AppLayout() {
  const { user } = useAuth()
  const location = useLocation()
  useTherapistRealtimeConnection()
  const [isMenuOpen, setIsMenuOpen] = useState(false)

  const displayName =
    [user?.first_name, user?.last_name].filter(Boolean).join(' ') || user?.email || 'Fizjoterapeuta'

  // Zamknij menu po zmianie trasy
  useEffect(() => {
    setIsMenuOpen(false)
  }, [location.pathname])

  // Zamykanie draweru klawiszem Escape
  useEffect(() => {
    if (!isMenuOpen) return
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        setIsMenuOpen(false)
      }
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [isMenuOpen])

  return (
    <div className="app-shell">
      <MFAEnforcementModal />
      <aside className="app-shell__sidebar" aria-label="Nawigacja główna">
        <div className="app-shell__header-row">
          <Link
            to="/"
            className="app-shell__brand"
            aria-label="PhysioCare - Pulpit"
            onClick={() => setIsMenuOpen(false)}
          >
            <img
              className="app-shell__mark"
              src="/brand/sygnet.png"
              alt=""
              width={48}
              height={48}
            />
            <div>
              <p className="app-shell__product">PhysioCare</p>
              <p className="app-shell__product-sub">Panel fizjoterapeuty</p>
            </div>
          </Link>

          <button
            type="button"
            className="app-shell__toggle"
            aria-label={isMenuOpen ? 'Zamknij nawigację' : 'Otwórz nawigację'}
            aria-expanded={isMenuOpen}
            aria-controls="app-shell-drawer"
            onClick={() => setIsMenuOpen((prev) => !prev)}
          >
            <svg
              width="24"
              height="24"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
              aria-hidden="true"
            >
              {isMenuOpen ? (
                <>
                  <line x1="18" y1="6" x2="6" y2="18" />
                  <line x1="6" y1="6" x2="18" y2="18" />
                </>
              ) : (
                <>
                  <line x1="3" y1="12" x2="21" y2="12" />
                  <line x1="3" y1="6" x2="21" y2="6" />
                  <line x1="3" y1="18" x2="21" y2="18" />
                </>
              )}
            </svg>
          </button>
        </div>

        <div
          id="app-shell-drawer"
          className={`app-shell__drawer ${isMenuOpen ? 'app-shell__drawer--open' : ''}`.trim()}
        >
          <nav className="app-shell__nav">
            {NAV.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.end}
                className={({ isActive }) =>
                  isActive ? 'app-shell__link app-shell__link--active' : 'app-shell__link'
                }
                onClick={() => setIsMenuOpen(false)}
              >
                {item.label}
              </NavLink>
            ))}
          </nav>

          <div className="app-shell__footer">
            <NavLink
              to="/profile"
              className="app-shell__identity"
              aria-label={`Profil: ${displayName}`}
              onClick={() => setIsMenuOpen(false)}
            >
              {user?.avatar_url ? (
                <AuthMediaImg path={user.avatar_url} className="app-shell__avatar" />
              ) : (
                <span className="app-shell__avatar app-shell__avatar--fallback" aria-hidden="true">
                  {initials(user?.first_name, user?.last_name)}
                </span>
              )}
              <span className="app-shell__identity-text">
                <span className="app-shell__user">{displayName}</span>
                <span className="app-shell__role">Fizjoterapeuta</span>
              </span>
            </NavLink>
          </div>
        </div>
      </aside>

      {isMenuOpen ? (
        <div
          className="app-shell__backdrop"
          onClick={() => setIsMenuOpen(false)}
          aria-hidden="true"
        />
      ) : null}

      <div className="app-shell__main">
        <Outlet />
      </div>
    </div>
  )
}
