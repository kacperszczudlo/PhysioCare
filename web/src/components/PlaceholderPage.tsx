interface PlaceholderPageProps {
  title: string
  description: string
  phaseTask: string
}

export function PlaceholderPage({ title, description, phaseTask }: PlaceholderPageProps) {
  return (
    <section>
      <header className="page-header">
        <div className="page-header__text">
          <h1 className="page-header__title">{title}</h1>
          <p className="page-header__desc">{description}</p>
        </div>
      </header>
      <div className="placeholder-panel" role="status">
        <p className="placeholder-panel__label">W przygotowaniu</p>
        <p className="placeholder-panel__copy">
          Moduł zostanie podłączony w zadaniu <strong>{phaseTask}</strong> planu rozwoju.
        </p>
      </div>
    </section>
  )
}
