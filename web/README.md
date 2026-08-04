# PhysioCare Web — panel fizjoterapeuty

React 19 + Vite + TypeScript. Komunikacja z backendem przez REST (`/api/v1`) i cookies JWT (`credentials: 'include'`).

## Uruchomienie

```powershell
cd web
npm install
npm run dev
```

Aplikacja: http://localhost:5173  
API (osobny terminal): `python manage.py runserver` w `backend/physiocare`.

W dev Vite proxy przekierowuje `/api` → `http://localhost:8000`. Opcjonalnie ustaw `VITE_API_BASE_URL` w `.env.local` (szablon: `.env.example`).

## Skrypty

| Komenda | Opis |
|---------|------|
| `npm run dev` | Dev server |
| `npm run build` | Build produkcyjny |
| `npm run preview` | Podgląd builda |
| `npm run lint` | Oxlint |

## Struktura

```
src/
  api/          # apiClient + endpointy auth/terapeuta
  auth/         # AuthProvider, ProtectedRoute
  components/   # UI współdzielone
  layouts/      # App shell + auth shell
  pages/        # Widoki (route'y)
  styles/       # Tokeny OKLCH + global CSS
```

## Status (Faza 4)

- **4.1** Szkielet + routing + apiClient — gotowe
- **4.2** Auth (login / rejestracja PWZFz / reset) — gotowe
- **4.3** Harmonogram dzienny + drag & drop — gotowe
- **4.4–4.6** Karta pacjenta, ćwiczenia, profil — placeholdery
