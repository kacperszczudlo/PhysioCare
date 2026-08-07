import { Link, Outlet } from 'react-router-dom'

import './AuthLayout.css'

export function AuthLayout() {
  return (
    <div className="auth-layout">
      <div className="auth-layout__panel">
        <Link to="/login" className="auth-layout__brand">
          <span className="auth-layout__mark" aria-hidden="true" />
          PhysioCare
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
