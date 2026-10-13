import { Link } from 'react-router-dom'

import { useOptionalAuth } from '@/auth/AuthContext'
import { ACCOUNT_DELETION_MAILTO, DATA_CONTROLLER } from '@/content/dataController'

/**
 * Strona procedury usuwania konta i danych osobowych użytkownika (zgodność z Google Play & Apple App Store).
 */
export function AccountDeletionPage() {
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

  const homeLabel = !isAuthenticated
    ? 'Logowanie'
    : user?.role === 'ADMIN'
      ? 'Panel administratora'
      : user?.role === 'PATIENT'
        ? 'Portal pacjenta'
        : 'Wróć do pulpitu'

  return (
    <article className="legal-doc">
      <header className="legal-doc__header">
        <h1>Usuwanie konta PhysioCare</h1>
        <p className="legal-doc__meta">Wymóg Google Play Data Safety / Apple Account Deletion</p>
        <p className="legal-doc__lede">
          Konto pacjenta można zamknąć z aplikacji mobilnej. Jeśli nie masz aplikacji, wniosek
          składasz przez tę stronę.
        </p>
      </header>

      <section className="legal-doc__section">
        <h2>1. W aplikacji (zalecane)</h2>
        <p>
          Zaloguj się w aplikacji mobilnej PhysioCare → Ustawienia → „Wniosek o usunięcie konta”.
          Potwierdź decyzję i podaj powód rezygnacji. System wyłącza konto, anonimizuje dane osobowe
          (adres e-mail staje się wolny do ponownej rejestracji), wyłącza powiadomienia push i
          unieważnia sesje. Dane medyczne mogą pozostać przez okres retencji wymagany prawem.
        </p>
      </section>

      <section className="legal-doc__section">
        <h2>2. Bez aplikacji (ten URL)</h2>
        <p>
          Wyślij wiadomość e-mail do Administratora ({DATA_CONTROLLER.name}) na adres{' '}
          <a href={ACCOUNT_DELETION_MAILTO}>{DATA_CONTROLLER.email}</a> z tematem „Usunięcie konta
          PhysioCare”. Podaj adres e-mail konta oraz - jeśli pamiętasz - imię i nazwisko. Nie
          prosimy o hasło.
        </p>
        <p>
          Zweryfikujemy tożsamość w zakresie niezbędnym i potwierdzimy przyjęcie wniosku. Usunięcie
          nie jest tożsame z samym „zawieszeniem” profilu - chodzi o skasowanie danych, o ile prawo
          nie nakazuje ich dłuższego przechowywania (np. dokumentacja medyczna / roszczenia).
        </p>
      </section>

      <section className="legal-doc__section">
        <h2>3. Co się dzieje z danymi</h2>
        <ul>
          <li>dane konta i preferencje - usuwane po zakończeniu procedury,</li>
          <li>
            dane zdrowotne - usuwane lub anonimizowane z uwzględnieniem przepisów retencyjnych,
          </li>
          <li>
            tokeny sesji - unieważniane; w razie zewnętrznych procesorów żądanie jest propagowane w
            zakresie umów powierzenia.
          </li>
        </ul>
      </section>

      <div className="legal-doc__actions">
        <Link to="/privacy">Polityka prywatności</Link>
        <Link to={homePath}>{homeLabel}</Link>
      </div>
    </article>
  )
}
