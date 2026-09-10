import { Link, NavLink, Outlet } from 'react-router-dom'

import { useAuth } from '@/auth/AuthContext'
import { AuthMediaImg } from '@/components/AuthMedia'
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

export function AppLayout() {
  const { user } = useAuth()
  useTherapistRealtimeConnection()
  const displayName =
    [user?.first_name, user?.last_name].filter(Boolean).join(' ') || user?.email || 'Fizjoterapeuta'

  return (
    <div className="app-shell">
      <aside className="app-shell__sidebar" aria-label="Nawigacja główna">
        <Link to="/" className="app-shell__brand" aria-label="PhysioCare - Pulpit">
          <img className="app-shell__mark" src="/brand/sygnet.png" alt="" width={48} height={48} />
          <div>
            <p className="app-shell__product">PhysioCare</p>
            <p className="app-shell__product-sub">Panel fizjoterapeuty</p>
          </div>
        </Link>

        <nav className="app-shell__nav">
          {NAV.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              className={({ isActive }) =>
                isActive ? 'app-shell__link app-shell__link--active' : 'app-shell__link'
              }
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
      </aside>

      <div className="app-shell__main">
        <Outlet />
      </div>
    </div>
  )
}
