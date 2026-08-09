import { Link } from 'react-router-dom'

import { COOKIE_POLICY_META, COOKIE_SECTIONS } from '@/content/cookiePolicy'

export function CookiePolicyPage() {
  return (
    <article className="legal-doc">
      <header className="legal-doc__header">
        <h1>{COOKIE_POLICY_META.title}</h1>
        <p className="legal-doc__meta">
          Wersja {COOKIE_POLICY_META.version} · {COOKIE_POLICY_META.effectiveDate}
        </p>
        <p className="legal-doc__lede">
          Informacja o cookies i technologiach w urządzeniu końcowym (PKE art. 399–400) dla
          PhysioCare.
        </p>
      </header>

      {COOKIE_SECTIONS.map((section) => (
        <section key={section.id} id={section.id} className="legal-doc__section">
          <h2>{section.title}</h2>
          {section.paragraphs.map((text) => (
            <p key={text.slice(0, 48)}>{text}</p>
          ))}
          {'table' in section && section.table ? (
            <table className="legal-doc__table">
              <thead>
                <tr>
                  {section.table.headers.map((header) => (
                    <th key={header} scope="col">
                      {header}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {section.table.rows.map((row) => (
                  <tr key={row.join('|')}>
                    {row.map((cell) => (
                      <td key={cell}>{cell}</td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          ) : null}
        </section>
      ))}

      <div className="legal-doc__actions">
        <Link to="/privacy">Polityka prywatności</Link>
        <Link to="/login">Wróć do logowania</Link>
      </div>
    </article>
  )
}
