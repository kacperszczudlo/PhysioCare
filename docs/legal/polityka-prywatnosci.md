# Polityka prywatności PhysioCare

**Wersja:** 1.0  
**Data wejścia w życie:** 8 sierpnia 2026 r.  
**Ostatnia aktualizacja:** 8 sierpnia 2026 r.

Dokument stanowi warstwę pełnej informacji (art. 13 i 14 RODO). Skrócone podsumowanie znajduje się na początku; szczegóły — w kolejnych sekcjach. Polityka dotyczy aplikacji webowej (panel fizjoterapeuty) oraz aplikacji mobilnej (pacjent).

---

## Podsumowanie (warstwa skrócona)

| Temat | W skrócie |
|-------|-----------|
| Kto przetwarza dane | Kacper Szczudło (ADO); kontakt: kacper.szczudlo@gmail.com |
| Po co | Świadczenie usług PhysioCare: konto, wizyty, dokumentacja fizjoterapeutyczna, ćwiczenia. |
| Jakie dane | Dane konta, kontaktowe, opcjonalnie PESEL; dane zdrowotne w karcie leczenia; dane techniczne sesji. |
| Zgody | Wymagane: regulamin + dane medyczne. Opcjonalne: marketing, badania — osobne przełączniki, wycofanie w ustawieniach. |
| Cookies / urządzenie | Tylko technologie niezbędne do logowania i bezpieczeństwa (PKE). Brak SDK reklamowych i analityki behawioralnej. |
| Usunięcie konta | Wniosek w aplikacji mobilnej (pacjent) oraz strona WWW `/account-deletion`. |
| Twoje prawa | Dostęp, sprostowanie, usunięcie, ograniczenie, przenoszenie, sprzeciw, skarga do UODO. |

---

## 1. Administrator danych

**Administratorem danych osobowych** (ADO) w rozumieniu RODO jest:

> **Kacper Szczudło** (osoba fizyczna)  
> Forma: twórca systemu PhysioCare (projekt dyplomowy / demonstracyjny)  
> Korespondencja: wyłącznie elektroniczna  
> E-mail ds. prywatności / DSAR / usuwanie konta: **kacper.szczudlo@gmail.com**  
> NIP / KRS: nie dotyczy (brak działalności wpisanej do CEIDG/KRS w ramach tego projektu)

**Inspektor Ochrony Danych (IOD):** nie wyznaczono. W sprawach ochrony danych prosimy o kontakt pod adresem e-mail Administratora wskazanym powyżej.

PhysioCare jest systemem wspomagania gabinetu fizjoterapeutycznego (aplikacja webowa + mobilna + API). Administratorem danych jest twórca systemu wskazany powyżej.

---

## 2. Zakres stosowania

Polityka dotyczy przetwarzania danych w:

1. **Aplikacji webowej** PhysioCare (panel fizjoterapeuty),
2. **Aplikacji mobilnej** PhysioCare (pacjent),
3. **Backendzie API** obsługującym obie aplikacje,
4. Komunikacji e-mail związanej z kontem (np. reset hasła).

Nie dotyczy niezależnych stron trzecich, do których użytkownik może zostać przekierowany (np. mapa adresu wizyty w aplikacji systemowej urządzenia) — te podmioty stosują własne polityki.

---

## 3. Kategorie przetwarzanych danych

### 3.1. Dane konta i identyfikacyjne

- adres e-mail (login),
- imię i nazwisko,
- hasło (przechowywane wyłącznie w postaci skrótu kryptograficznego),
- rola użytkownika (`PATIENT` / `THERAPIST`),
- opcjonalny numer telefonu,
- dla fizjoterapeuty: numer PWZFz oraz oświadczenie zawodowe, opcjonalnie adres gabinetu, biogram, kursy, poziom kwalifikacji, lata doświadczenia, zdjęcie profilowe,
- dla pacjenta: opcjonalnie PESEL, zdjęcie profilowe, powiązanie z przypisanym terapeutą.

### 3.2. Dane dotyczące zdrowia (szczególna kategoria — art. 9 RODO)

W zakresie niezbędnym do prowadzenia dokumentacji fizjoterapeutycznej mogą być przetwarzane m.in.:

- epizody leczenia (m.in. kody ICD-10, rozpoznanie funkcjonalne, status, notatki podsumowujące),
- mapa dolegliwości / bólu (region ciała, skala VAS, charakter bólu, cele terapii),
- notatki z wizyt,
- zalecenia diagnostyczne, informacje o wyrobach medycznych / skierowaniach w zakresie przewidzianym systemem,
- dokumenty medyczne przesyłane do systemu (np. PDF),
- przypisane ćwiczenia oraz informacje o ich wykonaniu (compliance),
- dane wizyt: terminy, status, adres / lokalizacja wizyty, instrukcje przygotowania, notatki pacjenta, powód odwołania.

### 3.3. Dane techniczne i bezpieczeństwa

- tokeny sesji JWT (w przeglądarce: pliki cookie `access_token` / `refresh_token`; w aplikacji mobilnej: bezpieczny magazyn urządzenia, np. SecureStore),
- logi aplikacyjne ograniczone do metody, ścieżki, statusu, czasu trwania, identyfikatora użytkownika i identyfikatora żądania (**bez** zapisu haseł i bez celowego zbierania adresów IP w logach biznesowych),
- preferencje powiadomień w aplikacji (klucze preferencji, nie treść powiadomień push — o ile kanał push nie został włączony).

### 3.4. Czego nie zbieramy (stan na datę Polityki)

PhysioCare **nie** wykorzystuje obecnie:

- SDK reklamowych ani brokerów danych,
- analityki behawioralnej / profilowania marketingowego (np. Google Analytics, Firebase Analytics, Meta SDK),
- śledzenia cross-app / IDFA w celach reklamowych,
- geolokalizacji GPS w tle,
- dostępu do kontaktów, mikrofonu ani kamery urządzenia (poza ewentualnym wyborem zdjęcia profilowego inicjowanym przez użytkownika).

W razie wprowadzenia takich narzędzi Polityka zostanie zaktualizowana, a technologie niewymagalne do świadczenia usługi zostaną uruchomione dopiero po **granularnej zgodzie opt-in** (patrz § 6 i § 7).

---

## 4. Cele i podstawy prawne

| Cel | Przykłady danych | Podstawa prawna |
|-----|------------------|-----------------|
| Założenie i utrzymanie konta, uwierzytelnienie | e-mail, hasło, imię, nazwisko, rola | art. 6 ust. 1 lit. b RODO (umowa / świadczenie usługi) |
| Świadczenie funkcji gabinetu (wizyty, ćwiczenia, dokumenty) | dane wizyt, ćwiczenia, dokumenty | art. 6 ust. 1 lit. b RODO |
| Prowadzenie dokumentacji fizjoterapeutycznej | dane zdrowotne z § 3.2 | art. 9 ust. 2 lit. a RODO (wyraźna zgoda) oraz — w zakresie wymaganym przepisami — art. 9 ust. 2 lit. h RODO |
| Bezpieczeństwo, zapobieganie nadużyciom, logi | dane techniczne sesji, logi | art. 6 ust. 1 lit. f RODO (prawnie uzasadniony interes: integralność i poufność systemu); interes ten nie obejmuje profilowania marketingowego |
| Reset hasła / komunikacja serwisowa | e-mail | art. 6 ust. 1 lit. b RODO |
| Marketing (jeśli włączony) | e-mail / telefon wg zakresu zgody | art. 6 ust. 1 lit. a RODO (zgoda opcjonalna) |
| Badania naukowe / rozwojowe (jeśli włączone) | dane wskazane w zgodzie | art. 6 ust. 1 lit. a oraz — gdy dotyczy zdrowia — art. 9 ust. 2 lit. a RODO |
| Dochodzenie / obrona roszczeń, obowiązki prawne | dane rozliczeniowe i archiwalne w niezbędnym zakresie | art. 6 ust. 1 lit. c i/lub f RODO |

**Minimalizacja danych:** przy rejestracji zbieramy wyłącznie pola niezbędne do działania usługi. Pola takie jak telefon czy PESEL są opcjonalne, o ile nie wynikają z odrębnego obowiązku prawnego lub decyzji użytkownika.

**Osoby małoletnie:** serwis nie jest kierowany do dzieci poniżej 16. roku życia w rozumieniu art. 8 RODO. Nie zbieramy świadomie danych małoletnich bez zgody opiekuna.

---

## 5. Zgody (RODO + dobra praktyka EROD 05/2020)

### 5.1. Zgody wymagane (pacjent)

Przy rejestracji pacjenta wymagane są osobne, aktywne oświadczenia:

1. **Akceptacja regulaminu** (`TERMS_REQUIRED`),
2. **Zgoda na przetwarzanie danych medycznych** (`MEDICAL_DATA_REQUIRED`).

Bez tych zgód konto pacjenta nie zostanie utworzone — są one niezbędne do świadczenia usługi dokumentacji fizjoterapeutycznej. Cofnięcie zgody na dane medyczne jest równoznaczne z żądaniem zakończenia korzystania z usługi i usunięcia konta (z zastrzeżeniem § 10 — okresy retencji wynikające z prawa).

### 5.2. Zgody opcjonalne (granularne)

Osobno, bez wiązania („bundled consent”):

- marketing (`MARKETING_OPTIONAL`),
- badania (`RESEARCH_OPTIONAL`).

Udzielenie i wycofanie jest możliwe w ustawieniach aplikacji mobilnej. Wycofanie jest tak samo proste jak udzielenie (przełącznik). Brak zgody opcjonalnej **nie** ogranicza podstawowych funkcji leczenia i wizyt.

### 5.3. Zasady, których przestrzegamy

Zgodnie z wytycznymi EROD dotyczącymi zgody oraz zakazem dark patterns (m.in. EDPB 03/2022, DSA):

- zgoda to wyraźne działanie potwierdzające (np. zaznaczenie checkboxa / przycisk) — **nie** scroll, bierność ani zamknięcie okna,
- nie stosujemy „cookie walls” uzależniających dostęp do usługi od zgód marketingowych / analitycznych,
- opcje akceptacji i odrzucenia technologii niewymaganych mają mieć **parytet wizualny**, gdy takie technologie zostaną wprowadzone,
- domyślnie technologie niewymagalne są wyłączone (**privacy by default / off by default**),
- nie stosujemy confirmshamingu ani ukrywania opcji wycofania zgody w „labiryncie” ustawień.

---

## 6. Pliki cookie i dostęp do informacji w urządzeniu końcowym (PKE)

Od 10 listopada 2024 r. kwestie dostępu do informacji w urządzeniu końcowym reguluje m.in. **Prawo komunikacji elektronicznej (PKE)**, w szczególności art. 399 i 400, przy standardach zgody jak w RODO.

### 6.1. Technologie niezbędne (bez dodatkowej zgody marketingowej)

Stosujemy wyłącznie technologie **niezbędne** do świadczenia usługi wyraźnie zażądanej przez użytkownika lub bezpieczeństwa transmisji / sesji:

| Technologia | Środowisko | Cel | Okres |
|-------------|------------|-----|-------|
| Cookie `access_token` | Web | Sesja zalogowanego użytkownika (JWT) | krótkotrwały (ok. 15 min, konfigurowalne) |
| Cookie `refresh_token` | Web | Odświeżanie sesji | do ok. 7 dni (konfigurowalne), rotacja |
| SecureStore / magazyn bezpieczny | Mobile | Przechowywanie tokenów JWT | do wylogowania / wygaśnięcia |

Szczegóły: [Polityka cookies](./polityka-cookies.md) oraz strona `/cookies` w aplikacji webowej.

### 6.2. Technologie niewymagalne

Obecnie **nie** instalujemy cookies analitycznych, reklamowych ani preferencyjnych śledzących. Gdyby miały się pojawić, uruchomienie nastąpi dopiero po **uprzedniej, granularnej zgodzie opt-in**, a biblioteki zewnętrzne (SDK) będą inicjalizowane **asynchronicznie** — dopiero po sygnale z warstwy zarządzania zgodami (CMP), nigdy automatycznie przy starcie aplikacji przed wyborem użytkownika.

---

## 7. Odbiorcy danych i podmioty przetwarzające

Dane mogą być powierzane lub udostępniane wyłącznie w niezbędnym zakresie:

- **przypisanemu fizjoterapeucie** — w zakresie karty pacjenta, wizyt, dokumentów i zaleceń (cel leczenia),
- **dostawcom hostingu / bazy danych / poczty e-mail** — na podstawie umów powierzenia (DPA), gdy środowisko produkcyjne korzysta z zewnętrznej infrastruktury,
- **organom publicznym** — wyłącznie gdy wymaga tego prawo.

Aktualny model referencyjny projektu: PostgreSQL, lokalne lub kontenerowe przechowywanie plików mediów, opcjonalnie hosting wskazany w dokumentacji wdrożeniowej (np. Railway / VPS / Cloudflare Pages / Expo EAS). Przed produkcją Administrator uzupełni listę konkretnych procesorów.

**Współadministrowanie:** w razie użycia SDK, które samodzielnie określają cele przetwarzania, stosunek prawny (powierzenie / współadministrowanie / odrębny administrator) zostanie opisany w aktualizacji Polityki oraz w umowach.

---

## 8. Transfer poza EOG

Domyślnie dążymy do przetwarzania danych na terenie **EOG**.

Jeżeli dojdzie do transferu poza EOG (w tym dostęp zdalny z państwa trzeciego do danych hostowanych w EOG — zgodnie z wytycznymi EROD dotyczącymi transferów), transfer odbędzie się wyłącznie przy zachowaniu rozdziału V RODO, w szczególności:

- decyzji o adekwatności (np. **EU–US Data Privacy Framework**, gdy odbiorca jest certyfikowany), lub
- **standardowych klauzul umownych (SCC)** wraz z oceną wpływu transferu (**TIA**), lub
- innych prawnych mechanizmów art. 46+ RODO.

Użytkownik zostanie poinformowany o konkretnych transferach w aktualizacji niniejszej Polityki.

---

## 9. Okres przechowywania

| Zbiór | Okres |
|-------|--------|
| Dane konta aktywnego | przez czas korzystania z usługi |
| Dane zdrowotne / dokumentacja | przez czas trwania relacji terapeutycznej oraz przez okres wynikający z przepisów regulujących dokumentację medyczną / dochodzenie roszczeń (nie dłużej niż potrzeba) |
| Tokeny sesji | do wygaśnięcia / wylogowania |
| Logi techniczne | przez okres niezbędny do bezpieczeństwa i diagnostyki (zasada minimalizacji) |
| Wnioski o usunięcie konta | do zakończenia procedury usunięcia oraz ewentualnej obrony roszczeń |
| Zgody | wraz z dowodem udzielenia/wycofania — przez okres niezbędny do wykazania zgodności |

Po zakończeniu okresu dane są usuwane lub anonimizowane, z wyjątkiem sytuacji, w których prawo nakazuje dłuższe przechowywanie.

---

## 10. Prawa osoby, której dane dotyczą

Masz prawo do:

1. **dostępu** do danych,
2. **sprostowania**,
3. **usunięcia** („prawo do bycia zapomnianym”) — z ograniczeniami ustawowymi,
4. **ograniczenia** przetwarzania,
5. **przenoszenia** danych (w zakresie art. 20 RODO),
6. **sprzeciwu** wobec przetwarzania opartego na art. 6 ust. 1 lit. f RODO,
7. **wycofania zgody** w dowolnym momencie (bez wpływu na legalność przetwarzania sprzed wycofania),
8. **skargi do UODO** (ul. Stawki 2, 00-193 Warszawa, [uodo.gov.pl](https://uodo.gov.pl)).

### 10.1. Realizacja w PhysioCare

- **Eksport danych (pacjent):** `POST /api/v1/me/data-export/` oraz przycisk w ustawieniach aplikacji mobilnej — zwraca profil i status zgód; zakres eksportu może być rozszerzany.
- **Usunięcie konta (pacjent):**
  - **w aplikacji** — „Wniosek o usunięcie konta” w ustawieniach,
  - **poza aplikacją (wymóg sklepów mobilnych)** — strona WWW `/account-deletion`,
  - wniosek jest rejestrowany; usunięcie obejmuje dane konta i powiązane dane w systemach Administratora, z zastrzeżeniem obowiązków retencyjnych; w razie użycia zewnętrznych procesorów żądanie jest propagowane w zakresie umów (vendor propagation).
- **Zgody opcjonalne:** przełączniki w ustawieniach mobilnych.
- **DSAR:** kontakt e-mail do ADO; nie żądamy danych nadmiarowych wyłącznie w celu identyfikacji, jeśli użytkownik nie był wcześniej identyfikowany w ten sposób (art. 11 RODO).

Fizjoterapeuta może żądać usunięcia konta, kontaktując się z Administratorem (panel webowy może zostać uzupełniony o analogiczną ścieżkę).

---

## 11. Bezpieczeństwo (art. 32 RODO)

Stosujemy środki adekwatne do ryzyka, w tym:

- haszowanie haseł (bcrypt / mechanizmy Django),
- JWT z krótkim czasem życia access tokenu i rotacją refresh,
- cookies httpOnly / Secure (w konfiguracji produkcyjnej) oraz SameSite,
- bezpieczny magazyn tokenów w aplikacji mobilnej,
- autoryzację dostępu do zasobów pacjenta / terapeuty,
- ograniczenie treści logów (bez haseł),
- limity częstotliwości na wrażliwych endpointach auth,
- HTTPS w środowisku produkcyjnym.

Przy istotnych nowych funkcjach przetwarzających dane wrażliwe Administrator rozważa **DPIA** (ocenę skutków).

---

## 12. Privacy by Design i SDK

Zgodnie z zasadami Privacy by Design (minimalizuj, ukrywaj, separuj, abstrahuj):

- nie ładujemy trackingowych SDK przed zgodą,
- prowadzimy świadomość zależności (SBOM / rejestr komponentów w praktyce deweloperskiej),
- nowe funkcje wymagają aktualizacji rejestru czynności i — w razie potrzeby — Polityki.

---

## 13. Sklepy Apple App Store i Google Play

W zakresie publikacji mobilnej respektujemy m.in.:

- minimalizację danych przy rejestracji (Core Functionality / Guideline 5.1.1),
- zgodność deklaracji prywatności z faktycznym przetwarzaniem (App Privacy / Data Safety),
- **usuwanie konta w aplikacji** oraz **publiczny URL usuwania konta** (Google Play Data Safety; analogiczne wymagania Apple),
- brak równoważności ATT z zgodą RODO/PKE — w razie trackingu wymagane będą **oba** mechanizmy.

---

## 14. Zmiany Polityki

O istotnych zmianach poinformujemy w aplikacji lub pocztą e-mail oraz zaktualizujemy datę i numer wersji. Kontynuacja korzystania po wejściu zmian w życie, w zakresie, w jakim prawo tego wymaga, może wiązać się z ponownym potwierdzeniem określonych zgód.

---

## 15. Kontakt

Sprawy prywatności, DSAR i wnioski o usunięcie:

- e-mail ADO: **kacper.szczudlo@gmail.com**
- strona usuwania konta: `/account-deletion`
- pełna Polityka: `/privacy`
- Polityka cookies: `/cookies`

---

*Dokument uwzględnia RODO, PKE oraz praktyczne wymogi App Store / Google Play.*
