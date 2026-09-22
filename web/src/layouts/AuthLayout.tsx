import { Link, Outlet } from 'react-router-dom'

import './AuthLayout.css'

/**
 * Szablon widoku uwierzytelniania (logowanie, rejestracja, odzyskiwanie hasła) z bocznym panelem informacyjno-weryfikacyjnym.
 */
export function AuthLayout() {
  return (
    <div className="auth-layout">
      <div className="auth-layout__panel">
        <Link to="/login" className="auth-layout__brand" aria-label="PhysioCare">
          <img
            className="auth-layout__logo"
            src="/brand/logo.png"
            alt=""
            width={220}
            height={120}
          />
        </Link>
        <Outlet />
      </div>
      <aside className="auth-layout__aside" aria-hidden="true">
        <p className="auth-layout__aside-kicker">Gabinet w porządku</p>
        <p className="auth-layout__aside-copy">
          Harmonogram, karty pacjentów i ćwiczenia - w jednym spokojnym panelu.
        </p>
      </aside>
    </div>
  )
}
