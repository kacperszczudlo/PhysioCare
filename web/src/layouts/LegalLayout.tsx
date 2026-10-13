import { Link, NavLink, Outlet } from 'react-router-dom'

import { useOptionalAuth } from '@/auth/AuthContext'
import './LegalLayout.css'

/**
 * Szablon widoków prawno-informacyjnych (Polityka Prywatności, Pliki Cookie, Usuwanie Konta)
 * z dopracowaną nawigacją nagłówkową, spójną szerokością kontenera i detekcją stanu zalogowania.
 */
export function LegalLayout() {
  const auth = useOptionalAuth()
  const isAuthenticated = auth?.isAuthenticated ?? false
  const user = auth?.user ?? null

  const homePath = !isAuthenticated
    ? '/login'
    : user?.role === 'ADMIN'
      ? '/admin'
      : user?.role === 'PATIENT'
        ? '/patient-portal'
        : '/'

  const actionLabel = !isAuthenticated
    ? 'Zaloguj się'
    : user?.role === 'ADMIN'
      ? 'Panel administratora'
      : user?.role === 'PATIENT'
        ? 'Portal pacjenta'
        : 'Pulpit gabinetu'

  return (
    <div className="legal-layout">
      <header className="legal-layout__header">
        <div className="legal-layout__header-inner">
          <Link
            to={homePath}
            className="legal-layout__brand"
            aria-label={`PhysioCare - ${isAuthenticated ? 'Powrót do panelu' : 'Strona logowania'}`}
          >
            <img
              className="legal-layout__logo"
              src="/brand/logo.png"
              alt="PhysioCare"
              width={140}
              height={36}
            />
          </Link>

          <nav className="legal-layout__nav" aria-label="Dokumenty prawne">
            <NavLink
              to="/privacy"
              className={({ isActive }) =>
                `legal-layout__nav-link ${isActive ? 'legal-layout__nav-link--active' : ''}`
              }
            >
              Prywatność
            </NavLink>
            <NavLink
              to="/cookies"
              className={({ isActive }) =>
                `legal-layout__nav-link ${isActive ? 'legal-layout__nav-link--active' : ''}`
              }
            >
              Cookies
            </NavLink>
            <NavLink
              to="/account-deletion"
              className={({ isActive }) =>
                `legal-layout__nav-link ${isActive ? 'legal-layout__nav-link--active' : ''}`
              }
            >
              Usuwanie konta
            </NavLink>
          </nav>

          <div className="legal-layout__header-actions">
            <Link to={homePath} className="legal-layout__btn-login">
              {actionLabel}
            </Link>
          </div>
        </div>
      </header>

      <main className="legal-layout__main">
        <div className="legal-layout__card">
          <Outlet />
        </div>
      </main>

      <footer className="legal-layout__footer">
        <div className="legal-layout__footer-inner">
          <span>© {new Date().getFullYear()} PhysioCare. Wszelkie prawa zastrzeżone.</span>
          <nav className="legal-layout__footer-links" aria-label="Nawigacja prawna w stopce">
            <Link to="/privacy">Polityka prywatności</Link>
            <Link to="/cookies">Polityka cookies</Link>
            <Link to="/account-deletion">Usuwanie konta</Link>
          </nav>
        </div>
      </footer>
    </div>
  )
}
