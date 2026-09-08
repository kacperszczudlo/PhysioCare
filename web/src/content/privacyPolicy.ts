import { DATA_CONTROLLER } from '@/content/dataController'

export type LegalSection = {
  id: string
  title: string
  paragraphs: string[]
  bullets?: string[]
  table?: { headers: string[]; rows: string[][] }
}

export const PRIVACY_POLICY_META = {
  title: 'Polityka prywatności',
  version: '1.1',
  effectiveDate: '8 sierpnia 2026 r.',
  updatedAt: '8 września 2026 r.',
}

export const PRIVACY_SUMMARY_ROWS: { topic: string; summary: string }[] = [
  {
    topic: 'Kto przetwarza dane',
    summary: `${DATA_CONTROLLER.name} (ADO); kontakt: ${DATA_CONTROLLER.email}.`,
  },
  {
    topic: 'Po co',
    summary: 'Świadczenie PhysioCare: konto, wizyty, dokumentacja fizjoterapeutyczna, ćwiczenia.',
  },
  {
    topic: 'Jakie dane',
    summary:
      'Dane konta, kontaktowe, opcjonalnie PESEL; dane zdrowotne; dane techniczne sesji; przy pushu — token urządzenia.',
  },
  {
    topic: 'Zgody',
    summary:
      'Wymagane: regulamin + dane medyczne. Opcjonalne: marketing i badania — osobne przełączniki.',
  },
  {
    topic: 'Cookies / urządzenie',
    summary: 'Tylko technologie niezbędne do logowania (PKE). Brak SDK reklamowych i analityki.',
  },
  {
    topic: 'Usunięcie konta',
    summary: 'Wniosek w aplikacji mobilnej oraz strona /account-deletion.',
  },
  {
    topic: 'Twoje prawa',
    summary:
      'Dostęp, sprostowanie, usunięcie, ograniczenie, przenoszenie, sprzeciw, skarga do UODO.',
  },
]

export const PRIVACY_SECTIONS: LegalSection[] = [
  {
    id: 'admin',
    title: '1. Administrator danych',
    paragraphs: [
      `Administratorem danych osobowych (ADO) jest ${DATA_CONTROLLER.name} (${DATA_CONTROLLER.legalForm}), twórca systemu PhysioCare.`,
      DATA_CONTROLLER.correspondence,
      `E-mail ds. prywatności, DSAR i usuwania konta: ${DATA_CONTROLLER.email}. NIP/KRS: nie dotyczy.`,
      'Inspektor Ochrony Danych nie został wyznaczony — w sprawach ochrony danych prosimy o kontakt na e-mail Administratora.',
    ],
  },
  {
    id: 'scope',
    title: '2. Zakres stosowania',
    paragraphs: [
      'Polityka dotyczy aplikacji webowej (panel fizjoterapeuty), aplikacji mobilnej (pacjent), backendu API oraz komunikacji e-mail związanej z kontem (np. reset hasła).',
      'Nie obejmuje niezależnych usług zewnętrznych, do których możesz zostać przekierowany (np. mapa systemowa urządzenia).',
    ],
  },
  {
    id: 'data',
    title: '3. Kategorie przetwarzanych danych',
    paragraphs: [
      'Dane konta: e-mail, imię, nazwisko, hasło (wyłącznie skrót), rola, opcjonalny telefon; u fizjoterapeuty także PWZFz, biogram, adres gabinetu i pokrewne pola profilu; u pacjenta opcjonalnie PESEL i powiązanie z fizjoterapeutą.',
      'Dane zdrowotne (art. 9 RODO): epizody leczenia, mapa bólu (VAS), notatki, dokumenty, ćwiczenia i compliance, dane wizyt.',
      'Dane techniczne: tokeny JWT (cookies web lub SecureStore na mobile), ograniczone logi aplikacyjne (bez haseł), preferencje powiadomień. Przy włączonych powiadomieniach systemowych — token Expo (bez treści klinicznej w komunikacie).',
      'Stan na datę Polityki: nie używamy SDK reklamowych, analityki behawioralnej, śledzenia IDFA, GPS w tle ani dostępu do kontaktów/mikrofonu.',
    ],
  },
  {
    id: 'legal-bases',
    title: '4. Cele i podstawy prawne',
    paragraphs: [
      'Świadczenie usługi i konto — art. 6 ust. 1 lit. b RODO.',
      'Dokumentacja fizjoterapeutyczna (dane zdrowotne) — art. 9 ust. 2 lit. a RODO (wyraźna zgoda) oraz w zakresie wymaganym przepisami art. 9 ust. 2 lit. h RODO.',
      'Bezpieczeństwo i logi — art. 6 ust. 1 lit. f RODO (nie obejmuje profilowania marketingowego).',
      'Marketing i badania — wyłącznie na podstawie osobnej zgody (art. 6 ust. 1 lit. a; dla zdrowia także art. 9 ust. 2 lit. a).',
      'Stosujemy minimalizację danych. Serwis nie jest kierowany do dzieci poniżej 16. roku życia (art. 8 RODO).',
    ],
  },
  {
    id: 'consent',
    title: '5. Zgody',
    paragraphs: [
      'Pacjent przy rejestracji potwierdza osobno akceptację regulaminu oraz zgodę na przetwarzanie danych medycznych. Bez nich konto nie powstanie.',
      'Zgody opcjonalne (marketing, badania) są granularne, wyłączone domyślnie i wycofywalne w ustawieniach tak samo łatwo jak udzielane.',
      'Nie stosujemy zgody domniemanej (scroll, bierność), cookie walls ani dark patterns (m.in. EDPB 03/2022): brak asymetrii „zaakceptuj łatwo / odrzuć trudno”, confirmshamingu i ukrywania opcji prywatności.',
    ],
  },
  {
    id: 'cookies',
    title: '6. Cookies i dostęp do urządzenia (PKE)',
    paragraphs: [
      'Zgodnie z art. 399–400 PKE dostęp do informacji w urządzeniu końcowym wymaga uprzedniej zgody, z wyjątkiem technologii niezbędnych do usługi zażądanej przez użytkownika.',
      'PhysioCare używa cookies/magazynu niezbędnego do sesji JWT. Token powiadomień na telefonie zapisujemy dopiero po zgodzie systemu (PKE). Szczegóły: Polityka cookies (/cookies).',
      'Technologie niewymagalne — obecnie brak. W przyszłości: opt-in, parytet wizualny przycisków oraz asynchroniczna inicjalizacja SDK dopiero po zgodzie.',
    ],
  },
  {
    id: 'recipients',
    title: '7. Odbiorcy i procesorzy',
    paragraphs: [
      'Dane są dostępne dla przypisanego fizjoterapeuty w zakresie leczenia oraz — na podstawie DPA — dla dostawców hostingu, bazy i poczty, gdy infrastruktura jest zewnętrzna. Usługa Expo Push — tylko gdy pacjent włączy powiadomienia systemowe.',
      'Organom publicznym — wyłącznie gdy wymaga tego prawo. Lista konkretnych procesorów produkcyjnych zostanie uzupełniona przez ADO.',
    ],
  },
  {
    id: 'transfers',
    title: '8. Transfer poza EOG',
    paragraphs: [
      'Dążymy do przetwarzania w EOG. Transfer poza EOG (w tym dostęp zdalny z państwa trzeciego) tylko przy mechanizmach rozdziału V RODO: decyzja o adekwatności (np. EU–US DPF), SCC + TIA lub inne podstawy art. 46+ RODO.',
    ],
  },
  {
    id: 'retention',
    title: '9. Okres przechowywania',
    paragraphs: [
      'Dane konta — przez czas korzystania z usługi. Dokumentacja zdrowotna — przez czas relacji oraz okresy wynikające z przepisów. Tokeny sesji — do wygaśnięcia/wylogowania. Token Expo — do wylogowania lub wyłączenia powiadomień. Logi — tak krótko, jak to potrzebne do bezpieczeństwa.',
      'Po upływie okresu dane usuwamy lub anonimizujemy, chyba że prawo nakazuje dłuższe przechowywanie.',
    ],
  },
  {
    id: 'rights',
    title: '10. Twoje prawa',
    paragraphs: [
      'Przysługują Ci prawa dostępu, sprostowania, usunięcia, ograniczenia, przenoszenia, sprzeciwu, wycofania zgody oraz skargi do UODO (ul. Stawki 2, 00-193 Warszawa).',
      'W aplikacji: eksport (profil, wizyty, epizody, dokumenty, ćwiczenia, preferencje powiadomień, odcisk tokenu urządzenia) i wniosek o usunięcie konta (pacjent — zapis wniosku, dezaktywacja, unieważnienie sesji), przełączniki zgód opcjonalnych, strona /account-deletion gdy nie ma aplikacji.',
      'Nie żądamy nadmiarowych danych tylko po to, by Cię zidentyfikować, jeśli wcześniej nie byliśmy w stanie Cię zidentyfikować (art. 11 RODO).',
    ],
  },
  {
    id: 'security',
    title: '11. Bezpieczeństwo',
    paragraphs: [
      'Haszowanie haseł, JWT z krótkim access tokenem i rotacją refresh, cookies httpOnly/Secure w produkcji, SecureStore na mobile, autoryzacja zasobów, limity auth, HTTPS w produkcji. Przy ryzykownych funkcjach rozważamy DPIA.',
    ],
  },
  {
    id: 'stores',
    title: '12. App Store i Google Play',
    paragraphs: [
      'Respektujemy minimalizację danych przy rejestracji, zgodność deklaracji prywatności z rzeczywistością oraz wymóg usuwania konta w aplikacji i przez publiczny URL.',
      'Monit ATT (Apple) nie zastępuje zgody RODO/PKE — w razie trackingu wymagane są oba mechanizmy.',
    ],
  },
  {
    id: 'changes',
    title: '13. Zmiany Polityki',
    paragraphs: [
      'O istotnych zmianach poinformujemy w aplikacji lub e-mailem i zaktualizujemy wersję. W razie potrzeby poprosimy o ponowne potwierdzenie określonych zgód.',
    ],
  },
]
