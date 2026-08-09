export const COOKIE_POLICY_META = {
  title: 'Polityka cookies',
  version: '1.0',
  effectiveDate: '8 sierpnia 2026 r.',
}

export const COOKIE_SECTIONS = [
  {
    id: 'purpose',
    title: '1. Cel',
    paragraphs: [
      'Dokument wyjaśnia przechowywanie informacji i dostęp do urządzenia końcowego (przeglądarka / aplikacja) zgodnie z PKE (art. 399–400) oraz RODO.',
    ],
  },
  {
    id: 'essential',
    title: '2. Technologie niezbędne',
    paragraphs: [
      'Używamy wyłącznie technologii niezbędnych do zalogowanej sesji i bezpieczeństwa:',
    ],
    table: {
      headers: ['Nazwa', 'Środowisko', 'Cel', 'Czas życia'],
      rows: [
        ['access_token', 'Web (cookie httpOnly)', 'Sesja JWT', '~15 min (konfigurowalne)'],
        ['refresh_token', 'Web (cookie httpOnly)', 'Odświeżenie sesji', 'do ~7 dni, rotacja'],
        ['Tokeny SecureStore', 'Mobile', 'Sesja poza przeglądarką', 'do wylogowania / wygaśnięcia'],
      ],
    },
  },
  {
    id: 'optional',
    title: '3. Analityka i reklama',
    paragraphs: [
      'Obecnie nieużywane. Gdyby miały się pojawić: off by default, granularny opt-in, parytet wizualny „Akceptuj/Odrzuć” oraz asynchroniczna inicjalizacja SDK dopiero po zgodzie — bez cookie walls i zgody domniemanej.',
    ],
  },
  {
    id: 'manage',
    title: '4. Zarządzanie',
    paragraphs: [
      'Web: wylogowanie unieważnia sesję; możesz też usunąć cookies w przeglądarce. Mobile: wylogowanie czyści SecureStore. Zgody marketing/badania zarządzasz w ustawieniach aplikacji pacjenta.',
    ],
  },
] as const
