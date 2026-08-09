# Checklist E2E - krytyczne ścieżki PhysioCare

Manualna / półautomatyczna weryfikacja przed demem (Faza 6.4).  
Automatyczne wsparcie: Postman (`docs/postman/`), pytest backend.

## Przygotowanie

- [ ] PostgreSQL działa, migracje zastosowane (`python manage.py migrate`)
- [ ] Backend: `runserver` na `:8000`
- [ ] Web: `npm run dev` na `:5173`
- [ ] Mobile: `npx expo start` (emulator / urządzenie / Expo Go)
- [ ] `.env` ma spójne `VITE_API_BASE_URL` / `EXPO_PUBLIC_API_BASE_URL` / CORS

## Backend API (smoke)

- [ ] Collection Runner w Postmanie (`docs/postman/PhysioCare.json`) - happy pathy UC bez błędów
- [ ] `python scripts/run_tests.py` - pytest zielony

## Web - fizjoterapeuta

| # | Ścieżka | Oczekiwany rezultat |
|---|---------|---------------------|
| W1 | Rejestracja terapeuty (PWZFz) | Konto + automatyczne logowanie / redirect |
| W2 | Logowanie | Dostęp do pulpitu |
| W3 | Reset hasła | Mail w konsoli backendu + zmiana hasła działa |
| W4 | Pulpit / harmonogram | Lista wizyt dnia, D&D / formularz wizyty |
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
| M4 | Wizyty | Nadchodzące + archiwum |
| M5 | Szczegóły wizyty | Stack `visit/[id]` |
| M6 | Profil terapeuty | Stack `therapist/[id]` ze zdjęciem (jeśli ustawione) |
| M7 | Dokumentacja | Lista kliniczna (kierowanie / wyroby / recepta / odmowa / PDF) po wystawieniu przez terapeutę |
| M8 | Profil | Dane kontaktowe, avatar |
| M9 | Offline / błąd API | Banner offline + czytelny `NetworkError` / ErrorBanner, bez crasha i bez wylogowania |

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
