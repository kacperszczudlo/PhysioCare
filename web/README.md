# PhysioCare Web - Panel Fizjoterapeuty & Panel Administratora

Aplikacja webowa systemu PhysioCare, zbudowana w oparciu o **React 19**, **Vite** oraz **TypeScript**, obsługująca role **Fizjoterapeuty** (`THERAPIST`) oraz **Administratora** (`ADMIN`) ze strażnikami tras RBAC.

Komunikacja z backendem odbywa się poprzez REST API (`/api/v1`) przy użyciu bezpiecznych ciasteczek JWT (`credentials: 'include'`). Aplikacja obsługuje odświeżanie w czasie rzeczywistym (Server-Sent Events: `GET /api/v1/me/events/` z automatycznym proxy Vite) dla live aktualizacji Harmonogramu i Pulpitu.

---

## Uruchomienie lokalne

```powershell
cd web
npm.cmd install
npm.cmd run dev
```

- **Adres aplikacji:** `http://localhost:5173`
- **Wymagany backend:** Uruchomione API na porcie 8000 (`python manage.py runserver` w katalogu `backend/physiocare`).

### Konfiguracja środowiska (`.env.local`)

W środowisku deweloperskim proxy Vite automatycznie przekierowuje zapytania `/api` oraz `/media` na `http://localhost:8000`.

W przypadku logowania przez Google należy ustawić zmienną:

```env
VITE_GOOGLE_CLIENT_ID=<Web Client ID>
```

Ten sam klient musi być skonfigurowany w `GOOGLE_CLIENT_IDS` na backendzie.

---

## Funkcjonalności Panelu WWW

### 🩺 Panel Fizjoterapeuty (`/`)
- **Autoryzacja i Profil Terapeuty:** Logowanie z weryfikacją numeru PWZFz, rejestracja, reset hasła kodem e-mail oraz zarządzenie profilem gabinetu.
- **Harmonogram Dzienny:** Interaktywny kalendarz wizyt z obsługą przeciągnij i upuść (drag & drop), zmianami statusów i filtrowaniem.
- **Kartoteka Pacjenta:** Pełna historia leczenia, wpisy epizodów, mapa bólów (skala VAS), dokumenty kliniczne i zgody RODO.
- **Baza Ćwiczeń i Zalecenia:** Katalog ćwiczeń fizjoterapeutycznych oraz moduł przypisywania spersonalizowanych planów domowych pacjentom.
- **Realtime UI (SSE):** Automatyczne odświeżanie interfejsu przy zmianie statusu wizyty lub dodaniu dokumentu bez konieczności przeładowywania strony.

### 🛡️ Panel Administratora (`/admin`)
- **Pulpit Analityczny (Dashboard KPI):** Monitorowanie wielkości bazy użytkowników (podział Mobile/Web/Admin), frekwencji wizyt (show-up rate %), średniej ocen kliniki oraz aktywnych planów leczenia.
- **Zarządzanie Użytkownikami:** Paginowana lista, zaawansowane filtry ról i statusów, modal szczegółów (PWZF, 2FA, data), natychmiastowe blokowanie kont, wysyłka kodów resetu hasła oraz bezpieczny soft-delete RODO.
- **Zbiorczy Grafik Kliniki:** Wielostanowiskowy przegląd harmonogramu pracy i wizyt z nawigacją tygodniową oraz filtrami specjalistów.
- **Zespół i Efektywność:** Weryfikacja numerów PWZF, stopni kwalifikacji, statystyk zrealizowanych/odwołanych wizyt i wskaźników zadowolenia pacjentów.
- **Moderacja Opinii:** Przegląd komentarzy, kontrola widoczności publicznej z automatyczną rekalkulacją ocen fizjoterapeuty.

---

## Skrypty

| Komenda                    | Opis                                                        |
| :------------------------- | :---------------------------------------------------------- |
| `npm.cmd run dev`          | Uruchomienie serwera deweloperskiego Vite                   |
| `npm.cmd test`             | Uruchomienie testów jednostkowych i komponentowych (Vitest) |
| `npm.cmd run build`        | Budowanie wersji produkcyjnej (`dist/`)                     |
| `npm.cmd run preview`      | Podgląd wygenerowanego builda produkcyjnego                 |
| `npm.cmd run lint`         | Kontrola jakości kodu (ESLint + Oxlint)                     |
| `npm.cmd run lint:fix`     | Automatyczna naprawa błędów lintera                         |
| `npm.cmd run format`       | Formatowanie kodu (Prettier write)                          |
| `npm.cmd run format:check` | Weryfikacja formatowania kodu (Prettier check)              |

---

## Struktura projektu

```
src/
  api/          # Klient HTTP (apiClient) oraz definicje endpointów
  auth/         # Kontekst autoryzacji (AuthProvider) oraz ochrona ścieżek (ProtectedRoute)
  components/   # Współdzielone komponenty UI (AsyncState, Modal, Field, BodyMap...)
  layouts/      # Szablony układu strony (App shell + Auth shell)
  pages/        # Widoki aplikacji (Harmonogram, Pacjenci, Ćwiczenia, Profil...)
  realtime/     # Obsługa Server-Sent Events (SSE client + event bus)
  styles/       # Przestrzeń barwna OKLCH oraz style globalne CSS
```
