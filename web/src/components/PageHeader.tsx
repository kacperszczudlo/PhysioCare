import type { ReactNode } from 'react'

import './PageHeader.css'

/** Właściwości nagłówka podstrony. */
interface PageHeaderProps {
  /** Główny tytuł widoku (h1). */
  title: string
  /** Opcjonalny podtytuł lub opis kontekstu strony. */
  description?: string
  /** Opcjonalne przyciski akcji nagłówkowych (np. "Dodaj pacjenta", "Filtruj"). */
  actions?: ReactNode
}

/**
 * Standardowy nagłówek podstrony z tytułem, opisem oraz sekcją przycisków akcji.
 *
 * @example
 * <PageHeader title="Kartoteka Pacjentów" description="Lista zarejestrowanych pacjentów" actions={<Button>Dodaj</Button>} />
 */
export function PageHeader({ title, description, actions }: PageHeaderProps) {
  return (
    <header className="page-header">
      <div className="page-header__text">
        <h1 className="page-header__title">{title}</h1>
        {description ? <p className="page-header__desc">{description}</p> : null}
      </div>
      {actions ? <div className="page-header__actions">{actions}</div> : null}
    </header>
  )
}
