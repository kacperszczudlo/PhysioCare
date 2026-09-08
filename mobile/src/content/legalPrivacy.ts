import { DATA_CONTROLLER } from '@/content/dataController'

export type LegalSection = {
  id: string
  title: string
  paragraphs: string[]
}

export const PRIVACY_META = {
  title: 'Polityka prywatności',
  version: '1.1',
  updatedAt: '8 września 2026 r.',
}

export const PRIVACY_SECTIONS: LegalSection[] = [
  {
    id: 'summary',
    title: 'W skrócie',
    paragraphs: [
      'Przetwarzamy dane konta, opcjonalnie telefon/PESEL oraz dane zdrowotne potrzebne do fizjoterapii.',
      'Zgody wymagane: regulamin + dane medyczne. Opcjonalne (marketing, badania) — osobne przełączniki w Ustawieniach.',
      'Nie używamy SDK reklamowych ani analityki behawioralnej. Sesja: SecureStore / cookies niezbędne (PKE).',
      'Usunięcie konta: Ustawienia → wniosek (konto zostaje wyłączone), albo strona WWW /account-deletion.',
    ],
  },
  {
    id: 'admin',
    title: 'Administrator',
    paragraphs: [
      `ADO: ${DATA_CONTROLLER.name} (${DATA_CONTROLLER.legalForm}). ${DATA_CONTROLLER.correspondence}`,
      `E-mail: ${DATA_CONTROLLER.email}. IOD nie wyznaczono. NIP/KRS: nie dotyczy.`,
    ],
  },
  {
    id: 'data',
    title: 'Jakie dane',
    paragraphs: [
      'Konto: e-mail, imię, nazwisko, hasło (skrót), rola, opcjonalny telefon, avatar.',
      'Zdrowie (art. 9 RODO): epizody, mapa bólu, notatki, dokumenty, ćwiczenia, wizyty.',
      'Techniczne: tokeny JWT w SecureStore, ograniczone logi bez haseł, preferencje powiadomień.',
      'Gdy włączysz powiadomienia systemowe: token Expo na serwerze (do wylogowania). Treść pusha jest ogólna, bez rozpoznania.',
    ],
  },
  {
    id: 'bases',
    title: 'Podstawy prawne',
    paragraphs: [
      'Umowa/usługa (art. 6 ust. 1 lit. b), wyraźna zgoda na dane medyczne (art. 9 ust. 2 lit. a), bezpieczeństwo (art. 6 ust. 1 lit. f), marketing/badania tylko na zgodzie opcjonalnej.',
    ],
  },
  {
    id: 'consent',
    title: 'Zgody i dark patterns',
    paragraphs: [
      'Zgoda to aktywne działanie — nie scroll ani bierność. Brak cookie walls i wiązania zgód opcjonalnych z dostępem do leczenia.',
      'Wycofanie zgód opcjonalnych jest tak samo proste jak ich udzielenie (przełączniki).',
    ],
  },
  {
    id: 'device',
    title: 'Urządzenie (PKE)',
    paragraphs: [
      'Dostęp do magazynu urządzenia tylko dla niezbędnej sesji. Token powiadomień — dopiero po zgodzie systemu. Trackingowe SDK — obecnie brak.',
    ],
  },
  {
    id: 'rights',
    title: 'Twoje prawa',
    paragraphs: [
      'Dostęp, sprostowanie, usunięcie, ograniczenie, przenoszenie, sprzeciw, skarga do UODO.',
      'W aplikacji: eksport danych (w tym preferencje powiadomień), wniosek o usunięcie, zarządzanie zgodami opcjonalnymi.',
    ],
  },
  {
    id: 'security',
    title: 'Bezpieczeństwo i sklepy',
    paragraphs: [
      'Haszowanie haseł, JWT, SecureStore, autoryzacja zasobów, HTTPS w produkcji.',
      'Spełniamy wymogi usuwania konta in-app oraz publicznego URL (Google Play / Apple).',
    ],
  },
]

export const COOKIE_SECTIONS: LegalSection[] = [
  {
    id: 'essential',
    title: 'Technologie niezbędne',
    paragraphs: [
      'Na mobile tokeny JWT trzymamy w SecureStore (lub bezpiecznym magazynie urządzenia) wyłącznie do utrzymania zalogowanej sesji.',
      'W wersji webowej analogiem są cookies httpOnly access_token / refresh_token.',
    ],
  },
  {
    id: 'optional',
    title: 'Analityka i reklama',
    paragraphs: [
      'Obecnie nieużywane. Gdyby miały się pojawić: domyślnie wyłączone, osobna zgoda opt-in, parytet „Akceptuj/Odrzuć”, SDK dopiero po zgodzie.',
    ],
  },
]
