# Przypadki użycia - PhysioCare

Rysunek: [diagrams/use-cases.drawio](diagrams/use-cases.drawio)

## Aktorzy

| Aktor | Opis |
|-------|------|
| **Pacjent** | Korzysta z aplikacji mobilnej |
| **Fizjoterapeuta** | Korzysta z panelu webowego |
| **System** | Automatyczne procesy (powiadomienia, walidacja) |

---

## UC-01 - Logowanie użytkownika

| Pole | Wartość |
|------|---------|
| Aktor | Pacjent / Fizjoterapeuta |
| Cel | Uzyskanie dostępu do własnego konta |
| Warunki wstępne | Konto istnieje w systemie |
| Przebieg | 1. Użytkownik podaje e-mail i hasło. 2. System sprawdza dane. 3. Wystawia JWT (cookie i/lub body). |
| Warunki końcowe | Sesja aktywna, przekierowanie do pulpitu |
| Wyjątki | E1: Błędne dane -> 401. E2: Konto nieaktywne -> 403. |

---

## UC-02 - Rejestracja pacjenta

| Pole | Wartość |
|------|---------|
| Aktor | Pacjent |
| Cel | Założenie konta z wymaganymi zgodami RODO |
| Warunki wstępne | Brak konta o danym e-mailu |
| Przebieg | 1. Pacjent wypełnia formularz (imię, nazwisko, e-mail, hasło). 2. Zaznacza zgody wymagane (regulamin, dane medyczne). 3. Przycisk aktywny dopiero po zgodach. 4. System tworzy User + PatientProfile. |
| Warunki końcowe | Konto utworzone, zgody zapisane z datą |
| Wyjątki | E1: E-mail zajęty -> 409. E2: Brak zgód -> 400. |

---

## UC-20 - Wybór i zarządzanie fizjoterapeutami (N:M)

| Pole | Wartość |
|------|---------|
| Aktor | Pacjent |
| Cel | Przeglądanie listy własnych fizjoterapeutów oraz wyszukiwanie i dodawanie nowych z bazy |
| Przebieg | 1. Pacjent przechodzi do zakładki **Specjaliści**. 2. Widzi listę aktualnie powiązanych fizjoterapeutów („Moi fizjoterapeuci”). 3. Może wyszukać nowego fizjoterapeutę w bazie (po nazwisku lub lokalizacji). 4. Kliknięcie „Dodaj” tworzy relację `PatientTherapistLink`. 5. Umówienie pierwszej wizyty u nowego fizjoterapeuty również automatycznie dodaje go do listy pacjenta. |
| Warunki końcowe | Pacjent może umawiać wizyty u wybranych fizjoterapeutów i przeglądać ich profile. |

---

## UC-03 - Rejestracja fizjoterapeuty

| Pole | Wartość |
|------|---------|
| Aktor | Fizjoterapeuta |
| Cel | Założenie konta gabinetu z weryfikacją PWZFz |
| Przebieg | 1. Formularz z numerem PWZFz i oświadczeniem. 2. System tworzy User (THERAPIST) + TherapistProfile. |
| Wyjątki | E1: PWZFz już zarejestrowany -> 409. |

---

## UC-04 - Reset hasła

| Pole | Wartość |
|------|---------|
| Aktor | Pacjent / Fizjoterapeuta |
| Przebieg | 1. Żądanie linku na e-mail. 2. Kliknięcie linku z tokenem. 3. Ustawienie nowego hasła. |

---

## UC-05 - Przegląd pulpitu pacjenta

| Pole | Wartość |
|------|---------|
| Aktor | Pacjent |
| Cel | Szybki podgląd terapii |
| Przebieg | 1. Karta najbliższej wizyty. 2. Lista ćwiczeń na dziś. 3. Skrót do historii leczenia. |

---

## UC-06 - Oznaczenie wykonania ćwiczenia (compliance)

| Pole | Wartość |
|------|---------|
| Aktor | Pacjent |
| Cel | Raportowanie realizacji zaleceń domowych |
| Przebieg | 1. Kliknięcie ćwiczenia na pulpicie. 2. System zapisuje ExerciseCompletion na dziś. 3. UI: haczyk + przekreślenie. |
| Powiązanie | Ćwiczenie musi być przypisane przez terapeutę (UC-15). |

---

## UC-07 - Przegląd i zarządzanie wizytami (pacjent)

| Pole | Wartość |
|------|---------|
| Aktor | Pacjent |
| Przebieg | 1. Zakładka nadchodzące / zakończone. 2. Wybór wolnego terminu z udostępnionego grafiku fizjoterapeuty. 3. Rezerwacja wizyty (status `PENDING_APPROVAL`). 4. Opcjonalnie: zmiana terminu (modal), odwołanie z potwierdzeniem. |
| Wyjątki | E1: Kolizja terminów -> 409. E2: Wybrany termin nie mieści się w aktywnych slotach dostępności fizjoterapeuty -> 400 Bad Request. |

---

## UC-08 - Pobranie dokumentacji medycznej

| Pole | Wartość |
|------|---------|
| Aktor | Pacjent |
| Przebieg | 1. Zakładka **Dokumentacja**. 2. Lista dokumentów klinicznych (kierowanie, wyroby, Recepta na Ruch, odmowy) oraz PDF-ów - widocznych automatycznie po wystawieniu przez terapeutę. 3. Szczegóły wpisu / otwarcie PDF. Dla wyrobów: opcjonalny 4-cyfrowy kod odbioru e-ZWM + disclaimer (model P1/NFZ). |
| Bezpieczeństwo | Tylko dokumenty przypisane do zalogowanego pacjenta. |
| Uwagi | Fizjoterapeuta nie wykonuje osobnego kroku „wyślij”; wystawienie w karcie pacjenta = publikacja dla pacjenta. Szkice (`DRAFT`) wyrobów / Recepty na Ruch nie są widoczne. Kod dostępu to kopia informacyjna z NFZ - PhysioCare nie wystawia formalnego e-ZWM ani recept na leki. |

---

## UC-09 - Zarządzanie zgodami i danymi osobowymi

| Pole | Wartość |
|------|---------|
| Aktor | Pacjent |
| Przebieg | 1. Zgody wymagane - tylko podgląd daty. 2. Zgody opcjonalne - przełączniki. 3. Eksport danych / wniosek o usunięcie konta. |

---

## UC-10 - Przegląd pulpitu terapeuty

| Pole | Wartość |
|------|---------|
| Aktor | Fizjoterapeuta |
| Przebieg | Widgety: liczba wizyt, nowi pacjenci, przypisane ćwiczenia. Lista najbliższych wizyt -> przejście do karty pacjenta. |

---

## UC-11 - Zarządzanie harmonogramem i dostępnością

| Pole | Wartość |
|------|---------|
| Aktor | Fizjoterapeuta |
| Przebieg | 1. Widok dzienny z nawigacją dat. 2. Zarządzanie grafikiem pracy (`/therapist/availabilities/`): dodawanie slotów cyklicznych tygodniowych (np. Pon 08:00-16:00) lub jednorazowych. 3. Dodanie wizyty (+ lub klik slotu). 4. Drag & drop zmiany godziny. 5. Automatyczny kolor wg typu terapii. |
| Wyjątki | E1: Kolizja terminów wizyt -> 409. E2: Nieprawidłowy przedział czasowy slotu -> 400. |

---

## UC-12 - Karta pacjenta i epizody leczenia

| Pole | Wartość |
|------|---------|
| Aktor | Fizjoterapeuta |
| Przebieg | 1. Wyszukiwarka pacjentów. 2. Wybór epizodu lub „+ Nowy epizod” (ICD-10). 3. Zmiana statusu epizodu. 4. Notatka z wizyty (tekst / załącznik). |
| Warunek | Dokumentacja starego epizodu nie miesza się z nowym. |

---

## UC-13 - Mapa ciała (Diagnostic Mapper)

| Pole | Wartość |
|------|---------|
| Aktor | Fizjoterapeuta |
| Przebieg | 1. Przełącznik przód/tył. 2. Zapisane regiony widać na sylwetce (kolor = VAS). 3. Klik regionu -> panel VAS, charakter bólu i cele leczenia. 4. Zapisz / Zaktualizuj / Usuń. |

---

## UC-14 - Zarządzanie wizytą z karty pacjenta

| Pole | Wartość |
|------|---------|
| Aktor | Fizjoterapeuta |
| Przebieg | Menu: przenieś termin, edytuj rodzaj/czas, odwołaj (z powodem). |

---

## UC-15 - Baza ćwiczeń i przypisanie

| Pole | Wartość |
|------|---------|
| Aktor | Fizjoterapeuta |
| Przebieg | 1. Filtrowanie kategorii. 2. Dodanie ćwiczenia (mp4/PDF). 3. Przypisanie: pacjent, dawkowanie, okres -> „Wyślij do aplikacji”. |

---

## UC-16 - Profil fizjoterapeuty

| Pole | Wartość |
|------|---------|
| Aktor | Fizjoterapeuta |
| Przebieg | Biogram, dynamiczna lista kursów (+/usuń), zmiana hasła. Dane widoczne w mobile (UC-17). |

---

## UC-17 - Podgląd profilu terapeuty (pacjent)

| Pole | Wartość |
|------|---------|
| Aktor | Pacjent |
| Przebieg | Wizytówka: biogram, oceny, kursy. Akcje: napisz / zadzwoń (deep link). |

---

## UC-18 - Preferencje i wysyłka powiadomień

| Pole | Wartość |
|------|---------|
| Aktor | Pacjent (przełączniki, zgoda systemowa na urządzeniu); **System** (wysyłka) |
| Przebieg | 1. Pacjent w Ustawieniach włącza typy: przypomnienie o wizycie, zmiana terminu, lista rezerwowa, ćwiczenia, nowy dokument. 2. Opcjonalnie udziela zgody systemowej na push (token Expo). 3. Zdarzenie w gabinecie (np. terapeuta zapisuje wizytę lub dokument) albo tick schedulera (`run_notification_scheduler`, co 15 min: okna 24h/2h oraz ćwiczenia na dziś). 4. System sprawdza preferencję: wyłączona → brak wysyłki; włączona + token → push; włączona bez tokenu → e-mail. 5. Tapnięcie pusha otwiera wizytę, dokumentację albo ćwiczenie. |
| Wyjątki | Wyciszenie preferencji przez użytkownika blokuje wysyłkę powiadomienia danym kanałem. Treść komunikatu powiadomienia jest zwięzła i zachowuje zasadę poufności (brak prezentacji szczegółowych danych medycznych ani kodów ICD-10 na ekranie blokady). |

---

## UC-19 - Katalog wyrobów medycznych

| Pole | Wartość |
|------|---------|
| Aktor | Fizjoterapeuta |
| Cel | Przegląd katalogu sprzętu ortopedycznego i pomocniczego wg uprawnień PWZFz |
| Przebieg | 1. Fizjoterapeuta otwiera katalog wyrobów. 2. System filtruje sprzęt zgodnie z poziomem kwalifikacji (Licencjat / Magister / Specjalista). 3. Możliwość wystawienia wniosku e-ZWM w karcie leczenia. |

---

## UC-20 - Wniosek o usunięcie konta i anonimizacja RODO

| Pole | Wartość |
|------|---------|
| Aktor | Pacjent / Fizjoterapeuta |
| Cel | Realizacja prawa do bycia zapomnianym (Art. 17 RODO) |
| Przebieg | 1. Użytkownik składa wniosek w ustawieniach prywatności. 2. System anonimizuje adres e-mail (`@deleted.invalid`), imię i nazwisko. 3. Usunięcie tokenów sesyjnych oraz deaktywacja profilu. |

---

## Ochrona Danych Osobowych i Medycznych (RODO Art. 9)

| Mechanizm | Opis Wdrożenia |
|-----------|----------------|
| **Szyfrowanie pól at-rest** | Dane wrażliwe (PESEL, notatki medyczne, diagnoza funkcjonalna, uzasadnienia skierowań) są przed zapisaniem do tabel w PostgreSQL automatycznie szyfrowane symetrycznym algorytmem Fernet (AES-128-CBC + HMAC SHA-256). |
| **Brak jawnego PESELu w BD** | Zapytania surowe SQL zwracają zaszyfrowany ciąg (`gAAAAA...`). Dekrypcja zachodzi wyłącznie w warstwie ORM po autoryzacji sesji. |
| **Maskowanie w API** | Endpointy API udostępniają numer PESEL oraz wpisy medyczne wyłącznie autoryzowanemu fizjoterapeucie (przypisanemu do pacjenta) oraz samemu pacjentowi. |

---

## Macierz UC × Moduł

| UC | Mobile | Web | API | BD |
|----|--------|-----|-----|-----|
| UC-01-04 | ✓ | ✓ | accounts | users |
| UC-05-09 | ✓ | - | patients, privacy | profiles, consents |
| UC-10-16 | - | ✓ | treatment, scheduling, exercises | episodes, visits |
| UC-17-18 | ✓ | - | therapists, notifications | profiles, prefs |
| UC-19-20 | ✓ | ✓ | therapists, privacy | medical_devices, deleted_users |
