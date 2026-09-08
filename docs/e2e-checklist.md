# Checklist E2E - krytyczne ścieżki PhysioCare

Manualna / półautomatyczna weryfikacja przed demem (Faza 6.4).  
Automatyczne wsparcie: Postman (`docs/postman/`), pytest backend.

## Przygotowanie

- [ ] PostgreSQL działa, migracje zastosowane (`python manage.py migrate`)
- [ ] Backend: `runserver` **lub** `uvicorn physiocare.asgi:application --reload --port 8000` (SSE) w `backend/physiocare`
- [ ] Web: `npm run dev` na `:5173` (proxy `/api` → backend; `VITE_API_BASE_URL` puste = same-origin)
- [ ] Mobile: `npx expo start` (emulator / urządzenie / Expo Go)
- [ ] `.env` ma spójne `EXPO_PUBLIC_API_BASE_URL` / CORS / `ALLOWED_HOSTS`

## Backend API (smoke)

- [ ] Collection Runner w Postmanie (`docs/postman/PhysioCare.json`) - happy pathy UC bez błędów
- [ ] `python scripts/run_tests.py` - pytest zielony (w tym `tests/notifications/test_sse*.py`)
- [ ] (Opcjonalnie) `curl -N -H "Authorization: Bearer <access>" http://localhost:8000/api/v1/me/events/` → ramki `ping`

## Web - fizjoterapeuta

| # | Ścieżka | Oczekiwany rezultat |
|---|---------|---------------------|
| W1 | Rejestracja terapeuty (PWZFz) | Konto + automatyczne logowanie / redirect |
| W2 | Logowanie | Dostęp do pulpitu |
| W3 | Reset hasła | Mail w konsoli backendu + zmiana hasła działa |
| W4 | Pulpit / harmonogram | Lista wizyt dnia, D&D / formularz wizyty |
| W4b | Live SSE (wizyty) | Otwarty Harmonogram lub Pulpit: zmiana wizyty po stronie pacjenta (prośba / odwołanie) odświeża UI **bez F5** |
| W5 | Pacjenci -> karta | Epizody, mapa ciała (region -> VAS -> cel leczenia), notatki |
| W6 | Ćwiczenia | CRUD + przypisanie pacjentowi |
| W7 | Profil | Podgląd / edycja + kod pacjenta + upload avatara (plik -> podgląd) |
| W8 | Sesja wygasła | Refresh cookie / redirect na login bez „wiszącego” UI |
| W9 | Stany UI | Loading / empty / error widoczne przy braku danych i błędzie API |

## Mobile - pacjent

| # | Ścieżka | Oczekiwany rezultat |
|---|---------|---------------------|
| M1 | Rejestracja + zgody RODO + kod terapeuty | Konto pacjenta powiązane z terapeutą, token w SecureStore |
| M2 | Logowanie | Tabs (pulpit / wizyty / dokumentacja / profil / ustawienia) |
| M3 | Pulpit | Compliance ćwiczeń, oznaczenie wykonania |
| M3b | Live SSE (pulpit) | Otwarty Pulpit: nowa wizyta / nowe ćwiczenie od terapeuty pojawia się **bez zmiany taba / pull** |
| M4 | Wizyty | Nadchodzące + archiwum |
| M4b | Live SSE (wizyty) | Otwarte Wizyty: zmiana statusu / terminu odświeża listę bez przełączania zakładek |
| M5 | Szczegóły wizyty | Stack `visit/[id]` |
| M6 | Profil terapeuty | Stack `therapist/[id]` ze zdjęciem (jeśli ustawione) |
| M7 | Dokumentacja | Lista kliniczna (kierowanie / wyroby / recepta / odmowa / PDF) po wystawieniu przez terapeutę |
| M7b | Live SSE (dokumenty) | Otwarta Dokumentacja: nowy PDF / pozycja kliniczna pojawia się bez pull-to-refresh |
| M8 | Profil | Dane kontaktowe, avatar |
| M9 | Offline / błąd API | Banner offline + czytelny `NetworkError` / ErrorBanner, bez crasha i bez wylogowania |
| M10 | Powiadomienia (UC-18) | Zgoda systemowa + token; OFF w ustawieniach → brak pusha/maila; ON → push (telefon) lub e-mail; tap otwiera właściwy ekran; `run_notification_scheduler --once` przy wizycie za ~24h i ćwiczeniu na dziś |
| M11 | Eksport danych | JSON zawiera zgody, wizyty, preferencje powiadomień i odcisk tokenu urządzenia (nie pełny token Expo) |

## Live UI (SSE)

Scenariusze Etapu 6 — obie aplikacje **zostają na tym samym ekranie** (bez F5 / bez zmiany taba / bez pull). Kontrakt: [api.md — Realtime SSE](api.md#realtime--sse-meevents).

| # | Akcja | Oczekiwany rezultat |
|---|--------|---------------------|
| L1 | Pacjent odwołuje / prosi o wizytę | Web: **Harmonogram** + **Pulpit** fizjo aktualizują się same |
| L2 | Fizjo dodaje / zatwierdza wizytę | Mobile: **Pulpit** (najbliższa wizyta) + **Wizyty** aktualizują się same |
| L3 | Fizjo upload PDF lub pozycja kliniczna | Mobile: **Dokumentacja** odświeża listę |
| L4 | Fizjo przypisuje ćwiczenie | Mobile: **Pulpit** → „Zalecenia na dziś” |
| L5 | Krótka utrata sieci / uśpienie apki, potem powrót | Stream reconnect (web EventSource / mobile AppState); kolejne mutacje znowu live **bez** ręcznego odświeżenia |

Automatyczna regresja publish/stream: `pytest tests/notifications/test_sse.py tests/notifications/test_sse_publish.py`.

## Cross-cutting

- [ ] Role: terapeuta nie ma dostępu do endpointów pacjenta i odwrotnie (403)
- [ ] Upload PDF (dokument) w limicie `MAX_UPLOAD_MB`
- [ ] Nagłówki `X-Request-ID` / `X-Response-Time-Ms` na odpowiedzi API
- [ ] Po wylogowaniu tokeny nie działają

## Regresja jakości

```powershell
# backend
cd backend; ..\backend\venv\Scripts\ruff.exe check physiocare tests
python -m pytest tests

# web
cd web; npm run lint; npm run format:check; npm run build

# mobile
cd mobile; npm run lint; npm run format:check
```

- [ ] Ruff / ESLint / Prettier / pytest / build web - zielone

## Wynik demo

Data: ________  Tester: ________  
Blokery: ________  
Uwagi: ________
