import { useEffect, useState } from 'react'
import { Link, NavLink, Outlet, useLocation } from 'react-router-dom'

import { useAuth } from '@/auth/AuthContext'
import {
  IconCalendar,
  IconDashboard,
  IconSettings,
  IconStar,
  IconStethoscope,
  IconUser,
  IconUsers,
} from '@/pages/admin/AdminIcons'
import './AdminLayout.css'

const NAV_ITEMS = [
  { to: '/admin', label: 'Pulpit', icon: IconDashboard, end: true },
  { to: '/admin/users', label: 'Użytkownicy', icon: IconUsers },
  { to: '/admin/schedules', label: 'Harmonogramy', icon: IconCalendar },
  { to: '/admin/therapists', label: 'Zespół fizjoterapeutów', icon: IconStethoscope },
  { to: '/admin/reviews', label: 'Moderacja opinii', icon: IconStar },
  { to: '/admin/profile', label: 'Mój profil', icon: IconUser },
  { to: '/admin/settings', label: 'Ustawienia', icon: IconSettings },
]

function initials(first?: string, last?: string): string {
  const value = `${first?.charAt(0) ?? ''}${last?.charAt(0) ?? ''}`.toUpperCase()
  return value || 'A'
}

/**
 * Szablon ramowy panelu administracyjnego PhysioCare.
 * Spójny z bazowym AppLayout (ten sam grid, typography, sidebar tokens).
 */
export function AdminLayout() {
  const { user } = useAuth()
  const location = useLocation()
  const [isMenuOpen, setIsMenuOpen] = useState(false)

  const displayName =
    [user?.first_name, user?.last_name].filter(Boolean).join(' ') || user?.email || 'Administrator'

  useEffect(() => {
    setIsMenuOpen(false)
  }, [location.pathname])

  useEffect(() => {
    if (!isMenuOpen) return
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setIsMenuOpen(false)
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [isMenuOpen])

  return (
    <div className="app-shell admin-shell">
      <aside className="app-shell__sidebar" aria-label="Nawigacja administracyjna">
        <div className="app-shell__header-row">
          <Link
            to="/admin"
            className="app-shell__brand"
            aria-label="PhysioCare - Panel Administratora"
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
              <p className="app-shell__product-sub">Panel administratora</p>
            </div>
          </Link>

          <button
            type="button"
            className="app-shell__toggle"
            aria-label={isMenuOpen ? 'Zamknij nawigację' : 'Otwórz nawigację'}
            aria-expanded={isMenuOpen}
            aria-controls="admin-shell-drawer"
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
          id="admin-shell-drawer"
          className={`app-shell__drawer ${isMenuOpen ? 'app-shell__drawer--open' : ''}`.trim()}
        >
          <nav className="app-shell__nav">
            {NAV_ITEMS.map((item) => {
              const Icon = item.icon
              return (
                <NavLink
                  key={item.to}
                  to={item.to}
                  end={item.end}
                  className={({ isActive }) =>
                    isActive ? 'app-shell__link app-shell__link--active' : 'app-shell__link'
                  }
                  onClick={() => setIsMenuOpen(false)}
                >
                  <Icon className="admin-nav__icon" />
                  <span>{item.label}</span>
                </NavLink>
              )
            })}
          </nav>

          <div className="app-shell__footer">
            <Link
              to="/admin/profile"
              className="admin-identity"
              title="Przejdź do profilu administratora"
              onClick={() => setIsMenuOpen(false)}
            >
              <span className="app-shell__avatar app-shell__avatar--fallback" aria-hidden="true">
                {initials(user?.first_name, user?.last_name)}
              </span>
              <div className="app-shell__identity-text">
                <span className="app-shell__user" title={displayName}>
                  {displayName}
                </span>
                <span className="app-shell__role admin-badge--role">Administrator</span>
              </div>
            </Link>
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

      <div className="app-shell__main admin-shell__main">
        <Outlet />
      </div>
    </div>
  )
}
