/**
 * @file dataController.ts
 * @description Dane kontaktowe oraz prawna tożsamość Administratora Danych Osobowych (ADO) aplikacji PhysioCare (zgodnie z wymogami RODO / GDPR).
 */

/**
 * Dane Administratora Danych Osobowych (ADO).
 */
export const DATA_CONTROLLER = {
  /** Imię i nazwisko administratora */
  name: 'Kacper Szczudło',
  /** Główny kontaktowy adres e-mail w sprawach prywatności */
  email: 'kacper.szczudlo@gmail.com',
  /** Formy prawna podmiotu */
  legalForm: 'osoba fizyczna',
  /** Instrukcja dotycząca drogi korespondencji */
  correspondence:
    'Korespondencja w sprawach ochrony danych wyłącznie elektroniczna na adres e-mail poniżej.',
  /** Inspektor Ochrony Danych (DPO) - null jeśli niewyznaczony */
  dpo: null as string | null,
} as const

/** Link mailto przygotowany do bezpośredniego wysłania zgłoszenia usunięcia konta pacjenta */
export const ACCOUNT_DELETION_MAILTO = `mailto:${DATA_CONTROLLER.email}?subject=${encodeURIComponent('Usunięcie konta PhysioCare')}`
