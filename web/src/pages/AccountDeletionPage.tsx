import { Link } from 'react-router-dom'

import { ACCOUNT_DELETION_MAILTO, DATA_CONTROLLER } from '@/content/dataController'

export function AccountDeletionPage() {
  return (
    <article className="legal-doc">
      <header className="legal-doc__header">
        <h1>Usuwanie konta PhysioCare</h1>
        <p className="legal-doc__meta">Wymóg Google Play Data Safety / Apple Account Deletion</p>
        <p className="legal-doc__lede">
          Możesz usunąć konto pacjenta z poziomu aplikacji mobilnej albo złożyć wniosek bez
          zainstalowanej aplikacji — tą stroną.
        </p>
      </header>

      <section className="legal-doc__section">
        <h2>1. W aplikacji (zalecane)</h2>
        <p>
          Zaloguj się w aplikacji mobilnej PhysioCare → Ustawienia → „Wniosek o usunięcie konta”.
          System rejestruje wniosek (odpowiedź API 202) i rozpoczyna procedurę usunięcia danych
          konta oraz powiązanych danych w systemach Administratora, z zastrzeżeniem obowiązków
          retencyjnych wynikających z prawa.
        </p>
      </section>

      <section className="legal-doc__section">
        <h2>2. Bez aplikacji (ten URL)</h2>
        <p>
          Wyślij wiadomość e-mail do Administratora ({DATA_CONTROLLER.name}) na adres{' '}
          <a href={ACCOUNT_DELETION_MAILTO}>{DATA_CONTROLLER.email}</a> z tematem „Usunięcie konta
          PhysioCare”. Podaj adres e-mail konta oraz — jeśli pamiętasz — imię i nazwisko. Nie prosimy
          o hasło.
        </p>
        <p>
          Zweryfikujemy tożsamość w zakresie niezbędnym i potwierdzimy przyjęcie wniosku. Usunięcie
          nie jest tożsame z samym „zawieszeniem” profilu — chodzi o skasowanie danych, o ile prawo
          nie nakazuje ich dłuższego przechowywania (np. dokumentacja medyczna / roszczenia).
        </p>
      </section>

      <section className="legal-doc__section">
        <h2>3. Co się dzieje z danymi</h2>
        <ul>
          <li>dane konta i preferencje — usuwane po zakończeniu procedury,</li>
          <li>dane zdrowotne — usuwane lub anonimizowane z uwzględnieniem przepisów retencyjnych,</li>
          <li>
            tokeny sesji — unieważniane; w razie zewnętrznych procesorów żądanie jest propagowane w
            zakresie umów powierzenia.
          </li>
        </ul>
      </section>

      <div className="legal-doc__actions">
        <Link to="/privacy">Polityka prywatności</Link>
        <Link to="/login">Logowanie</Link>
      </div>
    </article>
  )
}
