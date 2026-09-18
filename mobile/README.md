# PhysioCare Mobile - Aplikacja Pacjenta

Aplikacja mobilna dla pacjenta w systemie PhysioCare, zbudowana w oparciu o **Expo SDK 54** (React Native) oraz **TypeScript**.

Komunikacja z backendem odbywa się poprzez REST API (`/api/v1`) z autoryzacją JWT Bearer (przechowywaną w natywnym `SecureStore`). Aplikacja obsługuje odświeżanie w czasie rzeczywistym (Server-Sent Events: `GET /api/v1/me/events/`) dla wizyt, dokumentów i przypisanych ćwiczeń domowych.

---

## Sposoby uruchomienia

| Cel | Sposób uruchomienia | Push Notifications | Google Sign-In |
| :--- | :--- | :--- | :--- |
| **Szybki podgląd UI** (logowanie hasłem) | Expo Go: `npm.cmd run start:go` | Brak | Wyłączony (wymaga modułu natywnego) |
| **Pełna funkcjonalność** (Push + Google) | Native Build: `npm.cmd run android` | Tak (po zgodzie w OS) | Tak (`@react-native-google-signin`) |

Wszystkie tryby wymagają uruchomionego backendu (`python manage.py runserver 0.0.0.0:8000` w `backend/physiocare`).

### Konfiguracja środowiska (`.env`)

Skopiuj plik `.env.example` do `.env` i skonfiguruj adres API:

```env
EXPO_PUBLIC_API_BASE_URL=http://<IP-LAN-LUB-LOCALHOST>:8000/api/v1
```

| Środowisko | Wartość `EXPO_PUBLIC_API_BASE_URL` |
| :--- | :--- |
| Expo Web / iOS Simulator | `http://localhost:8000/api/v1` |
| Android Emulator | `http://10.0.2.2:8000/api/v1` |
| Telefon fizyczny (Go / Native) | `http://<IP-LAN-PC>:8000/api/v1` |

---

## Uruchomienie aplikacji

### A. Expo Go (Szybki start)

```powershell
cd mobile
npm.cmd install
npm.cmd run start:go
```

Zeskanuj kod QR w aplikacji **Expo Go** na telefonie.

### B. Native Android (Development Build)

Wymaga Android Studio (SDK, platform-tools, JDK 17/21).

```powershell
cd mobile
npm.cmd install
npm.cmd run android
```

---

## Funkcjonalności Aplikacji Mobilnej

- **Autoryzacja i Rejestracja:** Logowanie e-mail/hasło lub Google Sign-In, rejestracja z akceptacją zgód RODO, weryfikacja konta kodem e-mail oraz reset hasła.
- **Pulpit Pacjenta:** Podsumowanie najbliższej wizyty, wskaźnik realizacji ćwiczeń domowych (compliance) oraz szybkie akcje.
- **Moduł Wizyt:** Przegląd nadchodzących i archiwalnych wizyt, szczegóły wizyty, profil fizjoterapeuty oraz możliwość odwołania lub zmiany terminu.
- **Kliniczne Dokumenty:** Dostęp do kartotek, zaleceń, skierowań, zaświadczeń oraz programu "Recepta na Ruch".
- **Realizacja Ćwiczeń:** Dostęp do spersonalizowanego planu treningowego z instrukcjami wideo/opisowymi i oznaczaniem wykonania.
- **Powiadomienia i Ustawienia:** Powiadomienia Push (przypomnienia o wizycie 24h/2h przed), zarządzanie zgodami RODO i profil pacjenta.

---

## Powiadomienia Push (FCM) & Google Sign-In

1. **Google Sign-In:** Wymaga ustawienia `EXPO_PUBLIC_GOOGLE_WEB_CLIENT_ID` w `mobile/.env` oraz zarejestrowania ID w `GOOGLE_CLIENT_IDS` na backendzie.
2. **Push Notifications (Firebase Cloud Messaging):**
   - Pobierz `google-services.json` z Firebase Console dla pakietu `com.physiocare.patient`.
   - Umieść plik w katalogu `mobile/`.
   - Skonfiguruj klucz FCM V1 w panelu Expo dev wg dokumentacji Expo Push.

---

## Obsługa trybu Offline

- **Wskaźnik braku sieci:** Globalny baner powiadamiający o braku połączenia internetowego (moduł `NetInfo`).
- **Bezpieczna obsługa błędów:** Przechwytywanie błędu połączenia i zamiana na przyjazne komunikaty (`NetworkError`).
- **Cache sesji:** Dane autoryzacyjne i profil są bezpiecznie przechowywane w `SecureStore`, co pozwala na uruchomienie aplikacji bez dostępu do sieci.
- **Auto-refetch:** Automatyczne odświeżenie danych po powrocie połączenia.

---

## Skrypty i Struktura Katalogów

### Dostępne skrypty

| Komenda | Opis |
| :--- | :--- |
| `npm.cmd start` | Uruchomienie serwera Metro (Development Build) |
| `npm.cmd run start:go` | Uruchomienie pod aplikację Expo Go |
| `npm.cmd run android` | Kompilacja i uruchomienie na emulatorze/urządzeniu Android |
| `npm.cmd run ios` | Uruchomienie na symulatorze iOS (macOS) |
| `npm.cmd test` | Uruchomienie testów jednostkowych i komponentowych (Vitest) |
| `npm.cmd run lint` | Weryfikacja kodu (ESLint + TypeScript check) |
| `npm.cmd run format:check` | Weryfikacja formatowania (Prettier) |

### Struktura projektu

```
app/                 # Expo Router (auth + tabs + stack)
  (auth)/            # Ekrany logowania, rejestracji RODO, resetu
  (tabs)/            # Nawigacja zakładkowa (pulpit, wizyty, profil)
  visit/[id].tsx     # Szczegóły, zmiana oraz odwołanie wizyty
  therapist/[id].tsx # Kartoteka fizjoterapeuty
src/
  api/               # Klient HTTP oraz endpointy pacjenta
  auth/              # Kontekst autoryzacji (Bearer + SecureStore)
  network/           # Detekcja stanu połączenia (NetInfo)
  notifications/     # Obsługa zdalnych powiadomień Push
  components/        # Wycofywane komponenty UI (Button, AsyncState...)
  theme/             # System tokenów kolorystycznych (Olive Clinic)
```

---

## Rozwiązywanie problemów (Troubleshooting - Windows)

W przypadku problemów z długimi ścieżkami CMake (>260 znaków) w środowisku Windows podczas kompilacji natywnej Androida, zaleca się:
1. Ustawienie zmiennych środowiskowych `JAVA_HOME` i `ANDROID_HOME`.
2. Budowanie projektu w katalogu o krótkiej ścieżce (np. `%USERPROFILE%\p`) poprzez synchronizację plików źródłowych przy użyciu narzędzia `robocopy` (z wyłączeniem katalogu `android/` i `node_modules/`).
