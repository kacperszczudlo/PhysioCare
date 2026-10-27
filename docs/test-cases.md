# Przypadki testowe (Test Cases) - PhysioCare

Niniejszy dokument zawiera formalną specyfikację przypadków testowych dla platformy **PhysioCare** (panel webowy fizjoterapeuty i administratora, aplikacja mobilna pacjenta oraz backendowe API). Scenariusze zostały opracowane w oparciu o przypadki użycia zdefiniowane w [docs/use-cases.md](use-cases.md) oraz wymagania laboratoryjne przedmiotu *Testowanie i Jakość Oprogramowania*.

---

## Macierz pokrycia przypadków użycia (Traceability Matrix)

| ID Testu | Tytuł przypadku testowego | Powiązany Use Case | Moduł systemu | Rola / Aktor |
|:---|:---|:---|:---|:---|
| **TC001** | Logowanie użytkownika do panelu webowego z poprawnymi poświadczeniami | UC-01 | Web / Auth | Fizjoterapeuta |
| **TC002** | Odrzucenie próby logowania przy podaniu nieprawidłowego hasła | UC-01 | Web / Auth | Użytkownik nieuwierzytelniony |
| **TC003** | Rejestracja nowego pacjenta z wymaganymi zgodami RODO | UC-02 | Mobile / Auth | Pacjent |
| **TC004** | Rejestracja profilu fizjoterapeuty z walidacją numeru PWZFz | UC-03 | Web / Auth | Fizjoterapeuta |
| **TC005** | Prezentacja pulpitu klinicznego fizjoterapeuty i wskaźników dziennych | UC-10 | Web / Dashboard | Fizjoterapeuta |
| **TC006** | Dodanie cyklicznego slotu dostępności w grafiku pracy | UC-11 | Web / Schedule | Fizjoterapeuta |
| **TC007** | Utworzenie nowego epizodu leczenia i notatki w karcie pacjenta | UC-12 | Web / Treatment | Fizjoterapeuta |
| **TC008** | Naniesienie i edycja punktu bólu na mapie ciała (VAS) | UC-13 | Web / Body Map | Fizjoterapeuta |
| **TC009** | Przypisanie zaleceń domowych i ćwiczenia z bazy rehabilitacyjnej | UC-15 | Web / Exercises | Fizjoterapeuta |
| **TC010** | Oznaczenie realizacji ćwiczenia rehabilitacyjnego (Compliance) | UC-06 | Mobile / Exercises | Pacjent |
| **TC011** | Wyszukanie specjalisty i rezerwacja terminu wizyty przez pacjenta | UC-07, UC-20 | Mobile / Visits | Pacjent |
| **TC012** | Wgląd i pobranie dokumentacji medycznej w formacie PDF | UC-08 | Mobile / Documents | Pacjent |
| **TC013** | Wgląd administratora w pulpit wskaźników analitycznych kliniki (KPI) | UC-22 | Web / Admin | Administrator |
| **TC014** | Blokada konta użytkownika naruszającego regulamin (Deaktywacja) | UC-23 | Web / Admin | Administrator |
| **TC015** | Moderacja i ukrycie niecenzuralnej opinii pacjenta | UC-27 | Web / Admin | Administrator |
| **TC016** | Wymuszenie konfiguracji 2FA (TOTP Onboarding) dla personelu medycznego | UC-01, UC-03 | Web / Auth / Security | Fizjoterapeuta / Administrator |

---

## Szczegółowe scenariusze testowe

### TC001 - Logowanie użytkownika do panelu webowego z poprawnymi poświadczeniami

| Pole | Wartość |
|:---|:---|
| **ID** | `TC001` |
| **Tytuł** | Logowanie fizjoterapeuty do panelu webowego z poprawnymi poświadczeniami |
| **Powiązany UC** | UC-01 |
| **Rola / Aktor** | Fizjoterapeuta (`THERAPIST`) |
| **Warunki początkowe** | 1. Działający backend API na porcie 8000 oraz frontend na porcie 5173.<br>2. W bazie istnieje aktywne konto fizjoterapeuty z adresem e-mail `therapist@physiocare.test` i hasłem `TestPassword123!`.<br>3. Przeglądarka otwarta na stronie `http://localhost:5173/login`. |
| **Kroki testowe** | 1. Wprowadź adres `therapist@physiocare.test` w polu **Adres e-mail**.<br>2. Wprowadź hasło `TestPassword123!` w polu **Hasło**.<br>3. Kliknij przycisk **Zaloguj się**.<br>4. Poczekaj na odpowiedź serwera i przekierowanie. |
| **Oczekiwany rezultat** | 1. System wysyła żądanie `POST /api/v1/auth/login/` i zwraca kod odpowiedzi `200 OK`.<br>2. W nagłówku odpowiedzi ustawiane jest bezpieczne ciasteczko sesyjne `access_token` / `refresh_token`.<br>3. Użytkownik zostaje przekierowany pod adres `/` (pulpit fizjoterapeuty).<br>4. W pasku nawigacyjnym widoczne jest imię fizjoterapeuty oraz przycisk wylogowania. |

---

### TC002 - Odrzucenie próby logowania przy podaniu nieprawidłowego hasła

| Pole | Wartość |
|:---|:---|
| **ID** | `TC002` |
| **Tytuł** | Odrzucenie próby logowania przy podaniu nieprawidłowego hasła |
| **Powiązany UC** | UC-01 |
| **Rola / Aktor** | Użytkownik nieuwierzytelniony |
| **Warunki początkowe** | 1. Frontend webowy otwarty pod adresem `http://localhost:5173/login`.<br>2. W bazie danych istnieje użytkownik `therapist@physiocare.test`. |
| **Kroki testowe** | 1. Wprowadź poprawny adres e-mail `therapist@physiocare.test`.<br>2. Wprowadź błędne hasło `ZleHaslo999!`.<br>3. Kliknij przycisk **Zaloguj się**. |
| **Oczekiwany rezultat** | 1. API zwraca kod `401 Unauthorized`.<br>2. Token uwierzytelniający nie zostaje zapisany w magazynie przeglądarki ani ciasteczkach.<br>3. Użytkownik pozostaje na widoku logowania `/login`.<br>4. Wyświetlany jest czytelny komunikat błędu: *Nieprawidłowy e-mail lub hasło*. |

---

### TC003 - Rejestracja nowego pacjenta z wymaganymi zgodami RODO

| Pole | Wartość |
|:---|:---|
| **ID** | `TC003` |
| **Tytuł** | Rejestracja nowego pacjenta z wymaganymi zgodami RODO |
| **Powiązany UC** | UC-02 |
| **Rola / Aktor** | Nowy pacjent (`PATIENT`) |
| **Warunki początkowe** | 1. Aplikacja mobilna lub formularz rejestracji pacjenta otwarty na ekranie rejestracji.<br>2. Adres e-mail `nowy.pacjent@physiocare.test` nie występuje w tabeli `users`. |
| **Kroki testowe** | 1. Wypełnij pola: Imię (`Tomasz`), Nazwisko (`Testowy`), E-mail (`nowy.pacjent@physiocare.test`), Telefon (`+48500600700`).<br>2. Wprowadź hasło spełniające wymogi złożoności (min. 8 znaków, cyfra, wielka litera).<br>3. Zweryfikuj, że przycisk rejestracji jest nieaktywny przed zaznaczeniem checkboxów prawnych.<br>4. Zaznacz obowiązkowe zgody: akceptację regulaminu oraz zgodę na przetwarzanie szczególnych kategorii danych medycznych (Art. 9 RODO).<br>5. Kliknij przycisk **Zarejestruj się**. |
| **Oczekiwany rezultat** | 1. Formularz odblokowuje przycisk po zaznaczeniu zgód obligatoryjnych.<br>2. Żądanie `POST /api/v1/auth/register/` kończy się statusem `201 Created`.<br>3. W bazie danych powstaje rekord w tabeli `users` z rolą `PATIENT` oraz powiązany profil `PatientProfile`.<br>4. W tabeli zgód odnotowany zostaje dokładny znacznik czasu wyrażenia zgody RODO. |

---

### TC004 - Rejestracja profilu fizjoterapeuty z walidacją numeru PWZFz

| Pole | Wartość |
|:---|:---|
| **ID** | `TC004` |
| **Tytuł** | Rejestracja profilu fizjoterapeuty z walidacją numeru PWZFz |
| **Powiązany UC** | UC-03 |
| **Rola / Aktor** | Fizjoterapeuta (`THERAPIST`) |
| **Warunki początkowe** | 1. Otwarty formularz rejestracji personelu medycznego pod adresem `/register`.<br>2. E-mail `nowy.terapeuta@physiocare.test` nie jest zarejestrowany. |
| **Kroki testowe** | 1. Wybierz rolę **Fizjoterapeuta**.<br>2. Wprowadź błędny format numeru Prawa Wykonywania Zawodu Fizjoterapeuty (np. `ABC` lub 3 cyfry zamiast wymaganego formatu).<br>3. Zaobserwuj walidację formularza w czasie rzeczywistym.<br>4. Popraw numer PWZFz na prawidłowy 5-cyfrowy identyfikator (np. `78901`).<br>5. Uzupełnij pozostałe dane personalne i zatwierdź rejestrację. |
| **Oczekiwany rezultat** | 1. Błędny format PWZFz uniemożliwia wysłanie formularza i generuje wskazówkę walidacyjną.<br>2. Poprawny format pozwala na rejestrację – serwer odpowiada kodem `201 Created`.<br>3. Tworzony jest rekord fizjoterapeuty w tabeli `therapist_profiles`. |

---

### TC005 - Prezentacja pulpitu klinicznego fizjoterapeuty i wskaźników dziennych

| Pole | Wartość |
|:---|:---|
| **ID** | `TC005` |
| **Tytuł** | Prezentacja pulpitu klinicznego fizjoterapeuty i wskaźników dziennych |
| **Powiązany UC** | UC-10 |
| **Rola / Aktor** | Fizjoterapeuta (`THERAPIST`) |
| **Warunki początkowe** | 1. Fizjoterapeuta zalogowany w panelu webowym pod adresem `/`.<br>2. Na bieżący dzień zaplanowane są wizyty w module scheduling. |
| **Kroki testowe** | 1. Przejdź do strony głównej `/` (Pulpit).<br>2. Zweryfikuj kafelki podsumowujące: *Dzisiejsze wizyty*, *Aktywni pacjenci*, *Zadania rehabilitacyjne*.<br>3. Sprawdź listę najbliższych pacjentów i kliknij w nazwisko wybranego pacjenta. |
| **Oczekiwany rezultat** | 1. Pulpit ładuje się ze statusem HTTP 200 bez błędów w konsoli przeglądarki.<br>2. Wartości liczbowe odzwierciedlają aktualne rekordy w bazie.<br>3. Kliknięcie pacjenta powoduje płynne przejście do szczegółowej karty pacjenta pod adres `/patients/:id`. |

---

### TC006 - Dodanie cyklicznego slotu dostępności w grafiku pracy

| Pole | Wartość |
|:---|:---|
| **ID** | `TC006` |
| **Tytuł** | Dodanie cyklicznego slotu dostępności w grafiku pracy |
| **Powiązany UC** | UC-11 |
| **Rola / Aktor** | Fizjoterapeuta (`THERAPIST`) |
| **Warunki początkowe** | 1. Zalogowany fizjoterapeuta w widoku `/schedule`.<br>2. Dostępny kalendarz grafiku pracy. |
| **Kroki testowe** | 1. Kliknij przycisk **Zarządzaj dostępnością** / **Dodaj slot**.<br>2. Wybierz dzień tygodnia (np. *Środa*).<br>3. Zdefiniuj przedział czasowy: od `08:00` do `16:00`.<br>4. Zaznacz opcję slotu powtarzalnego.<br>5. Zapisz konfigurację przyciskiem **Zatwierdź**. |
| **Oczekiwany rezultat** | 1. Żądanie `POST /api/v1/therapist/availabilities/` wykonuje się z kodem `201 Created`.<br>2. Kalendarz natychmiast odświeża widok i prezentuje nowy blok dostępności w harmonogramie.<br>3. Pacjenci mogą wybierać godziny z tego przedziału podczas rezerwacji. |

---

### TC007 - Utworzenie nowego epizodu leczenia i notatki w karcie pacjenta

| Pole | Wartość |
|:---|:---|
| **ID** | `TC007` |
| **Tytuł** | Utworzenie nowego epizodu leczenia i notatki w karcie pacjenta |
| **Powiązany UC** | UC-12 |
| **Rola / Aktor** | Fizjoterapeuta (`THERAPIST`) |
| **Warunki początkowe** | 1. Fizjoterapeuta otworzył kartę pacjenta `/patients/:patientId`.<br>2. Pacjent posiada aktywną relację terapeutyczną. |
| **Kroki testowe** | 1. Przejdź do sekcji **Epizody leczenia** i kliknij **+ Nowy epizod**.<br>2. Wprowadź tytuł diagnozy (np. *Rehabilitacja po skręceniu stawu skokowego*) oraz kod ICD-10 (np. `S93.4`).<br>3. W polu notatki klinicznej wprowadź opis badania wstępnego i plan usprawniania.<br>4. Kliknij **Zapisz epizod**. |
| **Oczekiwany rezultat** | 1. System rejestruje epizod w bazie (`TreatmentEpisode`) statusem HTTP 201.<br>2. Notatka medyczna zostaje zaszyfrowana symetrycznie algorytmem Fernet (AES-128-CBC) w warstwie persystencji bazy danych.<br>3. Nowy epizod pojawia się na osi czasu pacjenta jako aktywny. |

---

### TC008 - Naniesienie i edycja punktu bólu na mapie ciała (VAS)

| Pole | Wartość |
|:---|:---|
| **ID** | `TC008` |
| **Tytuł** | Naniesienie i edycja punktu bólu na mapie ciała (VAS) |
| **Powiązany UC** | UC-13 |
| **Rola / Aktor** | Fizjoterapeuta (`THERAPIST`) |
| **Warunki początkowe** | 1. Otwarta karta pacjenta w zakładce **Mapa ciała** (Diagnostic Mapper).<br>2. Wybrany aktywny epizod leczenia. |
| **Kroki testowe** | 1. Przełącz sylwetkę anatomiczną na widok **Tył**.<br>2. Kliknij anatomiczny region lędźwiowy kręgosłupa.<br>3. W wysuwanym panelu bocznym ustaw poziom bólu na skali VAS: wartość `7/10`.<br>4. Zaznacz charakter bólu: *Promieniujący, ostry*.<br>5. Zapisz adnotację przyciskiem **Zapisz punkt bólu**. |
| **Oczekiwany rezultat** | 1. Punkt bólu zostaje zapisany w module leczenia (`treatment/body-map/`).<br>2. Sylwetka podświetla zaznaczony obszar kolorem odpowiadającym wartości skali VAS (np. intensywny odcień pomarańczowy/czerwony).<br>3. Odświeżenie strony zachowuje naniesiony znacznik. |

---

### TC009 - Przypisanie zaleceń domowych i ćwiczenia z bazy rehabilitacyjnej

| Pole | Wartość |
|:---|:---|
| **ID** | `TC009` |
| **Tytuł** | Przypisanie zaleceń domowych i ćwiczenia z bazy rehabilitacyjnej |
| **Powiązany UC** | UC-15 |
| **Rola / Aktor** | Fizjoterapeuta (`THERAPIST`) |
| **Warunki początkowe** | 1. Fizjoterapeuta otworzył katalog ćwiczeń `/exercises` lub kartę pacjenta.<br>2. W bazie ćwiczeń istnieje zestaw predefiniowanych ćwiczeń wideo/instruktażowych. |
| **Kroki testowe** | 1. Wyszukaj ćwiczenie *Mobilizacja stawu skokowego z taśmą*.<br>2. Kliknij opcję **Przypisz pacjentowi**.<br>3. Wybierz pacjenta z rozwijanej listy.<br>4. Ustaw parametry dawkowania: `3 serie po 12 powtórzeń`, `2 razy dziennie`, czas trwania: `14 dni`.<br>5. Zatwierdź przypisanie przyciskiem **Wyślij plan**. |
| **Oczekiwany rezultat** | 1. Tworzony jest rekord `ExerciseAssignment` powiązany z pacjentem i terapeutą.<br>2. Ćwiczenie staje się natychmiast widoczne w harmonogramie domowym pacjenta w aplikacji mobilnej. |

---

### TC010 - Oznaczenie realizacji ćwiczenia rehabilitacyjnego (Compliance)

| Pole | Wartość |
|:---|:---|
| **ID** | `TC010` |
| **Tytuł** | Oznaczenie realizacji ćwiczenia rehabilitacyjnego (Compliance) |
| **Powiązany UC** | UC-06 |
| **Rola / Aktor** | Pacjent (`PATIENT`) |
| **Warunki początkowe** | 1. Pacjent zalogowany w aplikacji mobilnej (lub Expo Web).<br>2. Na liście ćwiczeń na dzień dzisiejszy znajduje się przypisane ćwiczenie. |
| **Kroki testowe** | 1. Otwórz ekran główny aplikacji (Pulpit Pacjenta).<br>2. Odszukaj sekcję **Zadania na dziś**.<br>3. Kliknij w kafelek przypisanego ćwiczenia i zapoznaj się z instrukcją.<br>4. Kliknij przycisk **Oznacz jako wykonane**.<br>5. Opcjonalnie podaj poziom zmęczenia lub odczuwanego dyskomfortu. |
| **Oczekiwany rezultat** | 1. Aplikacja wysyła żądanie `POST /api/v1/exercises/completions/` z bieżącą datą.<br>2. Wskaźnik realizacji (compliance) na pulpicie pacjenta wzrasta procentowo.<br>3. Kafelek ćwiczenia zostaje oznaczony zielonym znacznikiem (ukończono). |

---

### TC011 - Wyszukanie specjalisty i rezerwacja terminu wizyty przez pacjenta

| Pole | Wartość |
|:---|:---|
| **ID** | `TC011` |
| **Tytuł** | Wyszukanie specjalisty i rezerwacja terminu wizyty przez pacjenta |
| **Powiązany UC** | UC-07, UC-20 |
| **Rola / Aktor** | Pacjent (`PATIENT`) |
| **Warunki początkowe** | 1. Pacjent zalogowany w aplikacji mobilnej.<br>2. Fizjoterapeuta posiada wolne sloty dostępności w kalendarzu. |
| **Kroki testowe** | 1. Przejdź do zakładki **Fizjoterapeuci**.<br>2. Wyszukaj profil fizjoterapeuty po nazwisku lub specjalizacji.<br>3. Otwórz kartę fizjoterapeuty i kliknij **Umów wizytę**.<br>4. Wybierz dogodną datę i wolną godzinę z kalendarza dostępności.<br>5. Wskaż typ usługi (np. *Konsultacja wstępna*) i zatwierdź rezerwację. |
| **Oczekiwany rezultat** | 1. Tworzony jest rekord wizyty ze statusem `PENDING_APPROVAL` lub `CONFIRMED`.<br>2. Wizyta pojawia się na liście nadchodzących spotkań w aplikacji pacjenta oraz w kalendarzu fizjoterapeuty.<br>3. Wybrany slot zostaje zablokowany dla innych pacjentów (zapobieganie kolizjom terminów). |

---

### TC012 - Wgląd i pobranie dokumentacji medycznej w formacie PDF

| Pole | Wartość |
|:---|:---|
| **ID** | `TC012` |
| **Tytuł** | Wgląd i pobranie dokumentacji medycznej w formacie PDF |
| **Powiązany UC** | UC-08 |
| **Rola / Aktor** | Pacjent (`PATIENT`) |
| **Warunki początkowe** | 1. Pacjent zalogowany w aplikacji mobilnej lub portalu pacjenta.<br>2. Fizjoterapeuta wystawił dokument (np. skierowanie, zalecenia lub wniosek o wyrób medyczny). |
| **Kroki testowe** | 1. Przejdź do zakładki **Dokumentacja**.<br>2. Zweryfikuj listę wystawionych dokumentów klinicznych.<br>3. Kliknij wybrany dokument, aby otworzyć widok podglądu.<br>4. Kliknij przycisk pobierania pliku PDF. |
| **Oczekiwany rezultat** | 1. Pacjent ma dostęp wyłącznie do własnych dokumentów medycznych (ochrona przed podatnościami IDOR/BOLA).<br>2. Plik PDF generowany/pobierany jest poprawnie z prawidłowymi nagłówkami `Content-Type: application/pdf`.<br>3. Dokument zawiera pełne dane gabinetu, numer PWZFz terapeuty oraz datę wystawienia. |

---

### TC013 - Wgląd administratora w pulpit wskaźników analitycznych kliniki (KPI)

| Pole | Wartość |
|:---|:---|
| **ID** | `TC013` |
| **Tytuł** | Wgląd administratora w pulpit wskaźników analitycznych kliniki (KPI) |
| **Powiązany UC** | UC-22 |
| **Rola / Aktor** | Administrator (`ADMIN`) |
| **Warunki początkowe** | 1. Użytkownik uwierzytelniony z rolą `ADMIN`.<br>2. Otwarty panel webowy pod adresem `/admin`. |
| **Kroki testowe** | 1. Przejdź do głównego widoku pulpitu administracyjnego `/admin`.<br>2. Zweryfikuj klocki analityczne KPI: łączna liczba pacjentów, liczba fizjoterapeutów, wskaźnik frekwencji (show-up rate %), średnia ocen kliniki.<br>3. Kliknij przycisk odświeżenia danych analitycznych. |
| **Oczekiwany rezultat** | 1. Żądania analityczne wykonują się ze statusem `200 OK`.<br>2. Interfejs renderuje wykresy i karty wskaźników bez przekroczenia limitów czasowych.<br>3. Próba wejścia na ten sam adres przez konto pacjenta lub fizjoterapeuty skutkuje blokadą `403 Forbidden`. |

---

### TC014 - Blokada konta użytkownika naruszającego regulamin (Deaktywacja)

| Pole | Wartość |
|:---|:---|
| **ID** | `TC014` |
| **Tytuł** | Blokada konta użytkownika naruszającego regulamin (Deaktywacja) |
| **Powiązany UC** | UC-23 |
| **Rola / Aktor** | Administrator (`ADMIN`) |
| **Warunki początkowe** | 1. Administrator zalogowany w panelu `/admin/users`.<br>2. Na liście użytkowników istnieje aktywne konto testowe. |
| **Kroki testowe** | 1. Wyszukaj użytkownika po adresie e-mail w wyszukiwarce modułu zarządzania.<br>2. Kliknij opcję przełączenia statusu konta (**Zablokuj konto** / **Deaktywuj**).<br>3. Potwierdź operację w oknie modalnym.<br>4. Sprawdź status konta w tabeli.<br>5. Spróbuj zalogować się na zablokowane konto w osobnym oknie incognito. |
| **Oczekiwany rezultat** | 1. Serwer ustawia flagę `is_active=False` w tabeli użytkownika.<br>2. Wszystkie aktywne tokeny refresh danego konta zostają natychmiast unieważnione (JWT blacklist).<br>3. Próba logowania na zablokowane konto kończy się błędem `403 Forbidden` z informacją o blokadzie. |

---

### TC015 - Moderacja i ukrycie niecenzuralnej opinii pacjenta

| Pole | Wartość |
|:---|:---|
| **ID** | `TC015` |
| **Tytuł** | Moderacja i ukrycie niecenzuralnej opinii pacjenta z rekalkulacją średniej ocen |
| **Powiązany UC** | UC-27 |
| **Rola / Aktor** | Administrator (`ADMIN`) |
| **Warunki początkowe** | 1. Administrator zalogowany w panelu moderacji `/admin/reviews`.<br>2. W systemie istnieje publicznie widoczna opinia wystawiona fizjoterapeucie. |
| **Kroki testowe** | 1. Odszukaj zgłoszoną opinię na liście recenzji.<br>2. Kliknij przełącznik widoczności opinii (**Ukryj recenzję**).<br>3. Sprawdź zaktualizowany status recenzji w panelu administracyjnym.<br>4. Otwórz publiczny profil ocenianego fizjoterapeuty jako pacjent. |
| **Oczekiwany rezultat** | 1. Żądanie moderacyjne aktualizuje pole `is_visible=False`.<br>2. Transakcyjny serwis domenowy automatycznie przelicza średnią ocen fizjoterapeuty z wyłączeniem ukrytej opinii.<br>3. Opinia natychmiast znika z profilu fizjoterapeuty widocznego dla pacjentów. |

---

### TC016 - Wymuszenie konfiguracji 2FA (TOTP Onboarding) dla personelu medycznego i administracji

| Pole | Wartość |
|:---|:---|
| **ID** | `TC016` |
| **Tytuł** | Wymuszenie konfiguracji 2FA (TOTP Onboarding) dla personelu medycznego i administracji |
| **Powiązany UC** | UC-01, UC-03 |
| **Rola / Aktor** | Fizjoterapeuta (`THERAPIST`) / Administrator (`ADMIN`) |
| **Warunki początkowe** | 1. Frontend webowy PhysioCare otwarty w przeglądarce.<br>2. Nowo zarejestrowany lub zalogowany użytkownik personelu medycznego bez aktywnego 2FA (`has_mfa = false`, `mfa_required = true`). |
| **Kroki testowe** | 1. Zaloguj się na konto fizjoterapeuty lub administratora bez skonfigurowanego 2FA.<br>2. Zaobserwuj natychmiastowe wyświetlenie nieodrzucalnego okna modalnego `MFAEnforcementModal` blokującego dostęp do pulpitów medycznych.<br>3. Zeskanuj zaprezentowany kod QR w aplikacji Authenticator (lub skopiuj tajny klucz TOTP).<br>4. Wprowadź wygenerowany 6-cyfrowy kod weryfikacyjny i kliknij **Aktywuj i przejdź dalej**.<br>5. Zweryfikuj krok 2 z prezentacją 10 jednorazowych kodów zapasowych i kliknij **Przejdź do systemu**.<br>6. Wyloguj się i zaloguj ponownie. |
| **Oczekiwany rezultat** | 1. Użytkownik nie może zamknąć okna konfiguracji 2FA klawiszem ESC ani kliknięciem w tło.<br>2. Endpoint `POST /api/v1/auth/2fa/enable/` zatwierdza kod i generuje kody ratunkowe.<br>3. Po zakończeniu konfiguracji stan sesji aktualizuje `has_mfa = true`, modal znika, a użytkownik uzyskuje pełny dostęp do systemu.<br>4. Przy kolejnym logowaniu system wymaga podania drugiego składnika (TOTP), zabezpieczając konto przed przejęciem. |

---

## Środowisko i narzędzia wykonawcze

* **Backend:** Python 3.12+, Django 6 REST Framework (`http://localhost:8000/api/v1/`)
* **Frontend Web:** React 19, Vite, TypeScript (`http://localhost:5173`)
* **Aplikacja Mobilna:** React Native, Expo SDK 57 (Pixel 8 Android Emulator / Expo Web `http://localhost:8081`)
* **Narzędzia automatyzacji testów:** Vitest, Pytest, Playwright / Chrome DevTools Protocol, ADB Platform Tools
