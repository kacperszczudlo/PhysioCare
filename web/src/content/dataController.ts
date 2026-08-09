/** Dane Administratora danych osobowych (ADO) — PhysioCare */
export const DATA_CONTROLLER = {
  name: 'Kacper Szczudło',
  email: 'kacper.szczudlo@gmail.com',
  /** Osoba fizyczna — brak NIP/KRS (projekt dyplomowy / demonstracyjny). */
  legalForm: 'osoba fizyczna',
  correspondence:
    'Korespondencja w sprawach ochrony danych wyłącznie elektroniczna na adres e-mail poniżej.',
  dpo: null as string | null,
} as const

export const PRIVACY_CONTACT_MAILTO = `mailto:${DATA_CONTROLLER.email}?subject=${encodeURIComponent('PhysioCare — ochrona danych')}`

export const ACCOUNT_DELETION_MAILTO = `mailto:${DATA_CONTROLLER.email}?subject=${encodeURIComponent('Usunięcie konta PhysioCare')}`
