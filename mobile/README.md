# PhysioCare Mobile - aplikacja pacjenta

Expo SDK **54** (React Native) + TypeScript. Komunikacja z backendem przez REST (`/api/v1`) i JWT Bearer (**SecureStore** na native).

> **Produkcja = native build (EAS / Expo Go na urządzeniu).**  
> `npm run web` / Expo web trzyma tokeny w `localStorage` — wyłącznie do lokalnego UI, nie jako klient produkcyjny.

> SDK 54 - zgodne ze sklepowym **Expo Go**.  
> „Aktualne” Expo Go ze sklepu **nie** obsługuje SDK 56/57 (nie są jeszcze w Play/App Store).

## Uruchomienie

```powershell
cd mobile
npm.cmd install
npm.cmd start
```

Wymaga działającego API: `python manage.py runserver` w `backend/physiocare`.

Skopiuj `.env.example` -> `.env` i ustaw `EXPO_PUBLIC_API_BASE_URL`:

| Środowisko               | URL                            |
| ------------------------ | ------------------------------ |
| Expo web / iOS simulator | `http://localhost:8000/api/v1` |
| Android emulator         | `http://10.0.2.2:8000/api/v1`  |
| Telefon (Expo Go)        | `http://<IP-LAN>:8000/api/v1`  |

Na Windowsie zawsze `npm.cmd` (nie `npm`) - ExecutionPolicy blokuje `npm.ps1`.

## Skrypty

| Komenda                               | Opis                       |
| ------------------------------------- | -------------------------- |
| `npm.cmd start`                       | Expo dev server            |
| `npm.cmd run android` / `ios` / `web` | Uruchomienie na platformie |
| `npm.cmd run lint`                    | ESLint + `tsc --noEmit`    |
| `npm.cmd run lint:fix`                | Autofix ESLint             |
| `npm.cmd run format`                  | Prettier (write)           |
| `npm.cmd run format:check`            | Prettier (check)           |

## Struktura

```
app/                 # Expo Router (auth + tabs + stack)
  (auth)/            # login, rejestracja RODO, reset
  (tabs)/            # pulpit, wizyty, profil
  visit/[id].tsx     # szczegóły / zmiana / odwołanie
  therapist/[id].tsx # wizytówka terapeuty
src/
  api/               # client + auth + patient endpoints
  auth/              # AuthProvider (Bearer + SecureStore)
  network/           # NetInfo - status offline / online
  components/        # Button, Field, AsyncState, OfflineBanner…
  theme/             # tokeny kolorystyczne (olive clinic)
```

## Offline

- Globalny banner „Brak połączenia z internetem” (NetInfo)
- Wywołania API zwracają czytelny `NetworkError` zamiast crasha
- Przywracanie sesji offline: tokeny nie są kasowane; używany jest cache użytkownika
- Po powrocie sieci profil jest odświeżany automatycznie

## Status (Faza 5)

- **5.1** Szkielet Expo + tabs/stack
- **5.2** Auth + zgody RODO przy rejestracji
- **5.3** Pulpit + compliance ćwiczeń
- **5.4** Wizyty (nadchodzące / archiwum)
- **5.5** Profil, dokumenty, powiadomienia, zgody
- **5.6** Szczegóły wizyty + profil terapeuty
- **5.7** Integracja z API (Bearer JWT)
