import { NavLink, Outlet } from 'react-router-dom'

import { useAuth } from '@/auth/AuthContext'
import './AppLayout.css'

const NAV: ReadonlyArray<{ to: string; label: string; end?: boolean }> = [
  { to: '/', label: 'Pulpit', end: true },
  { to: '/schedule', label: 'Harmonogram' },
  { to: '/patients', label: 'Pacjenci' },
  { to: '/exercises', label: 'Ćwiczenia' },
  { to: '/profile', label: 'Profil' },
]

export function AppLayout() {
  const { user, logout } = useAuth()
  const displayName = [user?.first_name, user?.last_name].filter(Boolean).join(' ') || user?.email

  return (
    <div className="app-shell">
      <aside className="app-shell__sidebar" aria-label="Nawigacja główna">
        <div className="app-shell__brand">
          <img
            className="app-shell__mark"
            src="/brand/sygnet.png"
            alt=""
            width={36}
            height={48}
          />
          <div>
            <p className="app-shell__product">PhysioCare</p>
            <p className="app-shell__product-sub">Panel terapeuty</p>
          </div>
        </div>

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
          <p className="app-shell__user">{displayName}</p>
          <button type="button" className="app-shell__logout" onClick={() => void logout()}>
            Wyloguj
          </button>
        </div>
      </aside>

      <div className="app-shell__main">
        <Outlet />
      </div>
    </div>
  )
}
