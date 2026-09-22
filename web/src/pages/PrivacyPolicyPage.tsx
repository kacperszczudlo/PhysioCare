import { Link } from 'react-router-dom'

import {
  PRIVACY_POLICY_META,
  PRIVACY_SECTIONS,
  PRIVACY_SUMMARY_ROWS,
} from '@/content/privacyPolicy'

/**
 * Strona z warstwową treścią Polityki Prywatności (RODO / RODO Medyczne / PKE) systemu PhysioCare.
 */
export function PrivacyPolicyPage() {
  return (
    <article className="legal-doc">
      <header className="legal-doc__header">
        <h1>{PRIVACY_POLICY_META.title}</h1>
        <p className="legal-doc__meta">
          Wersja {PRIVACY_POLICY_META.version} · Obowiązuje od {PRIVACY_POLICY_META.effectiveDate} ·
          Aktualizacja: {PRIVACY_POLICY_META.updatedAt}
        </p>
        <p className="legal-doc__lede">
          Warstwowa informacja o przetwarzaniu danych w PhysioCare (web + mobile): najpierw
          podsumowanie, poniżej pełny opis wymagany art. 13/14 RODO, z uwzględnieniem PKE oraz
          praktyk App Store / Google Play.
        </p>
      </header>

      <table className="legal-doc__summary">
        <caption className="sr-only">Podsumowanie polityki prywatności</caption>
        <thead>
          <tr>
            <th scope="col">Temat</th>
            <th scope="col">W skrócie</th>
          </tr>
        </thead>
        <tbody>
          {PRIVACY_SUMMARY_ROWS.map((row) => (
            <tr key={row.topic}>
              <th scope="row">{row.topic}</th>
              <td>{row.summary}</td>
            </tr>
          ))}
        </tbody>
      </table>

      {PRIVACY_SECTIONS.map((section) => (
        <section key={section.id} id={section.id} className="legal-doc__section">
          <h2>{section.title}</h2>
          {section.paragraphs.map((text) => (
            <p key={text.slice(0, 48)}>{text}</p>
          ))}
          {section.bullets ? (
            <ul>
              {section.bullets.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          ) : null}
        </section>
      ))}

      <div className="legal-doc__actions">
        <Link to="/cookies">Polityka cookies</Link>
        <Link to="/account-deletion">Usuwanie konta</Link>
        <Link to="/login">Wróć do logowania</Link>
      </div>
    </article>
  )
}
