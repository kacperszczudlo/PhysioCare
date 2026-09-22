# Wybór i Deklaracja Tematu - PhysioCare

**Zatwierdzony temat pracy dyplomowej (rok akademicki 2026/2027):**  
*System wspomagania zarządzania gabinetem fizjoterapeutycznym z wykorzystaniem aplikacji webowej i mobilnej.*

---

## Cel i założenia projektu

Głównym celem projektu jest wytworzenie zintegrowanego systemu telemedycznego wspomagającego obsługę gabinetu fizjoterapeutycznego, składającego się z:

1. **Panelu webowego fizjoterapeuty (SaaS):** obsługa harmonogramu wizyt, kartoteki pacjenta z mapą bólów (skala VAS), baza ćwiczeń domowych oraz tworzenie i przegląd dokumentacji klinicznej.
2. **Aplikacji mobilnej pacjenta:** dostęp do nadchodzących i archiwalnych terminów wizyt, weryfikacja realizacji zaleceń (compliance ćwiczeń domowych), dostęp do dokumentów klinicznych oraz zarządzanie zgodami RODO.
3. **Zintegrowanego serwera API (REST + SSE):** centralny backend komunikujący się z relacyjną bazą danych PostgreSQL i udostępniający dane w czasie rzeczywistym.

---

## Zakres funkcjonalny systemu

### 1. Aplikacja webowa (Panel Fizjoterapeuty)

| Moduł | Zakres funkcjonalny |
| :--- | :--- |
| **Autoryzacja** | Logowanie, rejestracja z weryfikacją numeru PWZFz, dwuskładnikowa autentykacja (TOTP/2FA), reset hasła |
| **Pulpit** | Statystyki dzienne gabinetu, lista najbliższych wizyt, szybkie akcje |
| **Harmonogram** | Kalendarz dzienny z interaktywną zmianą terminów (drag & drop), zarządzanie dostępnością |
| **Karta Pacjenta** | Epizody leczenia, rozpoznanie funkcjonalne (ICD-10), notatki kliniczne, mapa bólu (VAS) |
| **Baza Ćwiczeń** | Katalog multimedialny (wideo/PDF), zaawansowane filtrowanie, przydzielanie planów treningowych |
| **Profil Terapeuty** | Biogram zawodowy, wykaz ukończonych kursów i certyfikatów, ustawienia konta |

### 2. Aplikacja mobilna (Aplikacja Pacjenta)

| Moduł | Zakres funkcjonalny |
| :--- | :--- |
| **Autoryzacja** | Logowanie (hasło / Google Sign-In), rejestracja z akceptacją regulaminu i zgód RODO, reset hasła |
| **Pulpit** | Szczegóły najbliższej wizyty, zalecenia treningowe na dany dzień (compliance), szybki dostęp do profilu |
| **Wizyty** | Nadchodzące i archiwalne terminy, szczegóły wizyty, prośba o zmianę terminu lub odwołanie |
| **Dokumentacja** | Dostęp do kierowań, zaleceń sprzętowych (e-ZWM), skierowań "Recepta na Ruch" oraz zaświadczeń |
| **Profil i Zgody** | Dane kontaktowe, zarządzenie preferencjami powiadomień Push/E-mail, eksport i usunięcie konta RODO |

### 3. Warstwa serwerowa (Backend REST & Realtime)

- Centralna autoryzacja bezstanowa JWT z podziałem ról (`PATIENT` / `THERAPIST`).
- Szyfrowanie pól wrażliwych (PESEL, notatki medyczne) algorytmem symetrycznym AES-128 Fernet na poziomie bazy danych.
- Strumieniowanie powiadomień o zmianach stanu w czasie rzeczywistym (Server-Sent Events).
- Obsługa bezpiecznego przechowywania i pobierania plików medycznych.

---

## Stos technologiczny

| Warstwa | Technologia |
| :--- | :--- |
| **Backend** | Python 3.12+, Django 6, Django REST Framework |
| **Baza danych** | PostgreSQL 16 z rozszerzeniem `btree_gist` |
| **Aplikacja webowa** | React 19, Vite, TypeScript |
| **Aplikacja mobilna** | React Native, Expo SDK 54, TypeScript |
| **Autoryzacja & Szyfrowanie** | JWT (Cookie/Bearer), bcrypt, Cryptography Fernet (AES-128-CBC) |
| **Jakość i Testy** | Pytest, Pytest-Django, Vitest, Ruff, ESLint |
| **Kontrola wersji & CI** | Git, GitHub |

---

## Wykaz literatury i źródeł normatywnych

1. **Rozporządzenie Parlamentu Europejskiego i Rady (UE) 2016/679 (RODO)** z dnia 27 kwietnia 2016 r. w sprawie ochrony osób fizycznych w związku z przetwarzaniem danych osobowych.
2. **Prawo komunikacji elektronicznej (PKE)** – Ustawa z dnia 12 lipca 2024 r. (Dz.U. 2024 poz. 1221).
3. **Dokumentacja techniczna Django Software Foundation:** *Django Web Framework Documentation (v6.0)*, 2026.
4. **Dokumentacja techniczna Meta Platforms & Expo:** *React Native & Expo SDK 54 Documentation*, 2025/2026.

---

## Granice zakresu projektu (Scope Boundaries)

1. **Płatności online:** Obsługa płatności elektronicznych pozostaje poza zakresem v1 (rozliczenia realizowane są w gabinecie).
2. **Zaawansowany moduł opinii:** Wyświetlanie profilu fizjoterapeuty w aplikacji mobilnej zawiera ocenę zbiorczą; zaawansowane moderowanie recenzji jest opcjonalnym rozszerzeniem po etapie wdrożeniowym.
