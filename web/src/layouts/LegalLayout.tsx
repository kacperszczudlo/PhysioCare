import { Link, Outlet } from 'react-router-dom'

import './LegalLayout.css'

export function LegalLayout() {
  return (
    <div className="legal-layout">
      <header className="legal-layout__header">
        <Link to="/login" className="legal-layout__brand">
          <span className="legal-layout__mark" aria-hidden="true" />
          PhysioCare
        </Link>
        <nav className="legal-layout__nav" aria-label="Dokumenty prawne">
          <Link to="/privacy">Prywatność</Link>
          <Link to="/cookies">Cookies</Link>
          <Link to="/account-deletion">Usuwanie konta</Link>
        </nav>
      </header>
      <main className="legal-layout__main">
        <Outlet />
      </main>
    </div>
  )
}
