# PhysioCare Web - panel fizjoterapeuty

React 19 + Vite + TypeScript. Komunikacja z backendem przez REST (`/api/v1`) i cookies JWT (`credentials: 'include'`). Live odświeżanie Harmonogramu / Pulpitu: SSE `GET /api/v1/me/events/` (proxy Vite, cookie auth).

## Uruchomienie

```powershell
cd web
npm install
npm.cmd run dev
```

Aplikacja: http://localhost:5173  
API (osobny terminal): `python manage.py runserver` w `backend/physiocare` (SSE działa też na runserver; przy wielu streamach: uvicorn — patrz root README).

W dev Vite proxy przekierowuje `/api` i `/media` -> `http://localhost:8000` (stream SSE bez timeoutu). Opcjonalnie ustaw `VITE_API_BASE_URL` w `.env.local` (szablon: `.env.example`). Preferuj pusty / względny base URL, żeby EventSource szedł same-origin przez proxy.

Logowanie Google: ustaw `VITE_GOOGLE_CLIENT_ID` (Web Client ID) oraz `GOOGLE_CLIENT_IDS` na backendzie — bez tego przycisk Google jest ukryty.

Weryfikacja e-mail / reset hasła: kody 6 cyfr przez SMTP (lokalnie `EMAIL_BACKEND=console` albo Gmail App Password — patrz root `.env.example` / `docs/deployment.md`).

## Skrypty

| Komenda                | Opis              |
| ---------------------- | ----------------- |
| `npm run dev`          | Dev server        |
| `npm run build`        | Build produkcyjny |
| `npm run preview`      | Podgląd builda    |
| `npm run lint`         | ESLint + Oxlint   |
| `npm run lint:fix`     | Autofix ESLint    |
| `npm run format`       | Prettier (write)  |
| `npm run format:check` | Prettier (check)  |

## Struktura

```
src/
  api/          # apiClient + endpointy
  auth/         # AuthProvider, ProtectedRoute
  components/   # UI współdzielone (AsyncState, Modal, Field…)
  layouts/      # App shell + auth shell
  pages/        # Widoki (route'y)
  realtime/     # SSE client + bus (live wizyty)
  styles/       # Tokeny OKLCH + global CSS
```

## Status (Faza 4 - domknięta)

- **4.1** Szkielet + routing + apiClient
- **4.2** Auth (login / rejestracja PWZFz / reset)
- **4.3** Harmonogram dzienny + drag & drop
- **4.4** Karta pacjenta + Diagnostic Mapper
- **4.5** Baza ćwiczeń + przypisywanie
- **4.6** Profil fizjoterapeuty
- **4.7** Loading / error / empty + retry we wszystkich modułach
