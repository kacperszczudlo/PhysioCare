# Wybór tematu — PhysioCare

> Treść zgodna z zatwierdzonym formularzem zgłoszenia tematu pracy dyplomowej (rok akademicki 2026/2027).

## Temat

**System wspomagania zarządzania gabinetem fizjoterapeutycznym z wykorzystaniem aplikacji webowej i mobilnej.**

## Cel projektu

Zbudować spięty system obsługi gabinetu fizjoterapeutycznego, w skład którego wchodzą:

- **aplikacja webowa** (panel SaaS dla fizjoterapeutów),
- **aplikacja mobilna** (dla pacjentów),
- **serwer WWW** rozmawiający z relacyjną bazą.

Ma dać się układać grafik wizyt (czas zabiegu i dostępność specjalistów) oraz prowadzić dokumentację w logicznych **epizodach leczenia**.

## Zakres funkcjonalny

### Aplikacja webowa (fizjoterapeuta)

| Moduł | Zakres |
|-------|--------|
| Autoryzacja | Logowanie, rejestracja z numerem PWZFz, reset hasła |
| Pulpit | Statystyki dzienne, najbliższe wizyty, szybkie akcje |
| Harmonogram | Kalendarz dzienny, tworzenie/edycja wizyt, drag & drop |
| Karta pacjenta | Epizody leczenia, diagnoza, notatki z wizyt, mapa ciała (VAS) |
| Baza ćwiczeń | Katalog wideo/PDF, filtrowanie, przypisywanie pacjentom |
| Profil | Biogram, kursy zawodowe, hasło |

### Aplikacja mobilna (pacjent)

| Moduł | Zakres |
|-------|--------|
| Autoryzacja | Logowanie, rejestracja z zgodami RODO, reset hasła |
| Pulpit | Najbliższa wizyta, zalecenia na dziś (compliance), skrót do historii |
| Wizyty | Nadchodzące / zakończone, szczegóły, zmiana terminu, odwołanie |
| Profil | Dane kontaktowe, preferencje powiadomień, zgody RODO |
| Dokumentacja | Kierowanie, wyroby, Recepta na Ruch, odmowy i PDF — widoczne po wystawieniu przez terapeutę |
| Pod-widoki | Szczegóły wizyty, profil fizjoterapeuty |

### Wspólne (backend)

- Autoryzacja JWT z podziałem ról (`PATIENT` / `THERAPIST`)
- REST API jako jedyny punkt integracji web + mobile
- Przechowywanie plików medycznych (PDF, mp4)
- Zgody RODO i preferencje powiadomień
- Logowanie błędów i podstawowe metryki

## Proponowane technologie

| Warstwa | Technologia |
|---------|-------------|
| Backend | Python 3.12+, Django 5, Django REST Framework |
| Baza danych | PostgreSQL 16 |
| Aplikacja webowa | React 19, Vite, TypeScript |
| Aplikacja mobilna | React Native (Expo), TypeScript |
| Auth | JWT (access + refresh), bcrypt |
| Testy | pytest, pytest-django, Vitest, React Testing Library |
| Kontrola wersji | Git, GitHub |
| Diagramy | draw.io, Mermaid (w dokumentacji) |

## Literatura i narzędzia

- Dokumentacja Django / DRF / React / Expo
- OWASP ASVS (bezpieczeństwo API i danych medycznych)
- RODO - przetwarzanie danych zdrowotnych (zgody, eksport, usunięcie konta)
- Mockup UI: `mockup_systemu_fizjoterapii.tsx` (referencja wizualna)

## Ograniczenia MVP (świadome)

- Powiadomienia SMS poza zakresem v1. Push (Expo) i e-mail (gdy brak tokenu urządzenia); lista rezerwowa: preferencja bez zdarzenia domenowego.
- Oceny fizjoterapeuty - widok w mobile; pełny moduł opinii opcjonalny po MVP
- Analityka terapii - podstawowe widgety na pulpicie; zaawansowane raporty poza zakresem v1
