# PhysioCare Mobile - aplikacja pacjenta

Expo SDK **54** (React Native) + TypeScript. Komunikacja z backendem przez REST (`/api/v1`) i JWT Bearer (**SecureStore** na native). Live UI (SSE `GET /api/v1/me/events/`, Bearer/XHR): wizyty (Pulpit + Wizyty), dokumenty (Dokumentacja), ćwiczenia (`exercise.assigned` → Pulpit). Reconnect przy powrocie apki na foreground.

> **Produkcja i push na Androidzie = native build** (`expo run:android` / EAS).  
> Expo Go na Androidzie (SDK 53+) **nie** dostarcza zdalnego pusha. `npm run web` trzyma tokeny w `localStorage` - wyłącznie do lokalnego UI.

> SDK 54 - zgodne ze sklepowym **Expo Go**.  
> „Aktualne” Expo Go ze sklepu **nie** obsługuje SDK 56/57 (nie są jeszcze w Play/App Store).

Na Windowsie zawsze `npm.cmd` (nie `npm`) - ExecutionPolicy blokuje `npm.ps1`.

## Dwa sposoby uruchomienia

| Cel                                       | Jak                              | Push                         | Google Sign-In              |
| ----------------------------------------- | -------------------------------- | ---------------------------- | --------------------------- |
| Szybki UI, logowanie hasłem               | Expo Go + `npm.cmd run start:go` | Nie                          | Nie (przycisk wyłączony)    |
| Push + Google Sign-In                     | Native: `npm.cmd run android`    | Tak (po zgodzie w OS)        | Tak (RNGoogleSignin)        |

Oba wymagają działającego API: `python manage.py runserver` w `backend/physiocare`.

Skopiuj `.env.example` → `.env` i ustaw `EXPO_PUBLIC_API_BASE_URL`:

Dla logowania Google dodaj `EXPO_PUBLIC_GOOGLE_WEB_CLIENT_ID` (oraz opcjonalnie iOS/Android) — te same ID muszą być w `GOOGLE_CLIENT_IDS` na backendzie.

> **Google Sign-In** wymaga **native build** (`npm.cmd run android`) z `@react-native-google-signin/google-signin`. W Expo Go przycisk Google jest ukryty (brak natywnego modułu); logowanie hasłem działa.  
> Te same Client ID muszą być w `GOOGLE_CLIENT_IDS` na backendzie.

| Środowisko               | URL                            |
| ------------------------ | ------------------------------ |
| Expo web / iOS simulator | `http://localhost:8000/api/v1` |
| Android emulator         | `http://10.0.2.2:8000/api/v1`  |
| Telefon (Go albo native) | `http://<IP-LAN>:8000/api/v1`  |

Telefon i PC w tej samej sieci Wi‑Fi. W Django `ALLOWED_HOSTS` / CORS muszą znać ten IP.

---

## A. Expo Go (bez native builda)

```powershell
cd mobile
npm.cmd install
npm.cmd start
```

Zeskanuj QR w aplikacji **Expo Go**. Do codziennego UI to wystarczy. Powiadomienia na telefonie **nie** przyjdą jako push.

---

## B. Native Android (push, development build)

Powstaje aplikacja `com.physiocare.patient` (PhysioCare), nie Go. Po zalogowaniu rejestruje token Expo (`POST /api/v1/me/device-tokens/`).

### Wymagania

- [Android Studio](https://developer.android.com/studio) (SDK, platform-tools, NDK dociągnie Gradle)
- Telefon: **USB debugging** + zaufany ten komputer, albo emulator
- Windows: ninja (CMake 3.22) ucina ścieżki > 260 znaków. **Nie buduj** z `Documents\GitHub\PhysioCare\mobile`. Junction / `subst` nie działają (Gradle i tak bierze długą ścieżkę). Potrzebna **prawdziwa kopia** w `%USERPROFILE%\p`. **Nie** ustawiaj `CMAKE_OBJECT_PATH_MAX=180` - wtedy CMake nie skraca nazw `.o`.

### Zmienne użytkownika Windows (bez admina)

Ustaw raz na konto (nie wklejaj tego w każdej sesji):

```powershell
$jbr = "C:\Program Files\Android\Android Studio\jbr"
$sdk = "$env:LOCALAPPDATA\Android\Sdk"
[Environment]::SetEnvironmentVariable("JAVA_HOME", $jbr, "User")
[Environment]::SetEnvironmentVariable("ANDROID_HOME", $sdk, "User")

$userPath = [Environment]::GetEnvironmentVariable("Path", "User")
$add = @("$jbr\bin", "$sdk\platform-tools")
$parts = @($userPath -split ';' | Where-Object { $_ })
foreach ($p in $add) {
  if (-not ($parts | Where-Object { $_.TrimEnd('\') -ieq $p.TrimEnd('\') })) {
    $parts = @($p) + $parts
  }
}
[Environment]::SetEnvironmentVariable("Path", ($parts -join ';'), "User")
```

Ścieżka JBR jest z Android Studio. Inny JDK 17/21 też zadziała, byle `JAVA_HOME` wskazywał na katalog z `bin\java.exe`.

Po ustawieniu zmiennych **nie wystarczy nowa karta terminala w Cursorze / VS Code** - IDE trzyma stary `Path` z chwili startu. Zamknij Cursor całkowicie i otwórz ponownie, albo w **zewnętrznym** PowerShellu (Start → Windows PowerShell). Nie używaj `setx` do całego `Path` - obcina go do ~1024 znaków.

W sesji, która jeszcze nie widzi `java`, można ręcznie wczytać zmienne użytkownika:

```powershell
$env:JAVA_HOME = [Environment]::GetEnvironmentVariable("JAVA_HOME", "User")
$env:ANDROID_HOME = [Environment]::GetEnvironmentVariable("ANDROID_HOME", "User")
$env:Path = [Environment]::GetEnvironmentVariable("Path", "User") + ";" + [Environment]::GetEnvironmentVariable("Path", "Machine")
```

Sprawdzenie w **nowym** oknie:

```powershell
java -version
adb version
echo $env:JAVA_HOME
echo $env:ANDROID_HOME
```

### Build i wgranie na telefon (Windows)

Sprawdzone na tym repo: kopia w `%USERPROFILE%\p` (nie junction), **świeży** `android/` wygenerowany _w tej kopii_, potem `expo run:android`. `LongPathsEnabled` nie wystarcza. Po `robocopy` **usuń** skopiowany `android` - inaczej zostaje `autolinking.json` z GitHuba.

**Pierwszy raz / od zera:**

```powershell
$src = "C:\Users\kacpe\Documents\GitHub\PhysioCare\mobile"
$dst = "$env:USERPROFILE\p"
New-Item -ItemType Directory -Force -Path $dst | Out-Null
cmd /c "robocopy `"$src`" `"$dst`" /E /NFL /NDL /NJH /NJS /XD android .cxx .gradle"
if (Test-Path "$dst\android") { cmd /c rmdir /s /q "\\?\$dst\android" }
Set-Location $dst
npm.cmd run android
```

Kod `robocopy` 0-7 = sukces. Pierwszy Gradle: kilka-kilkanaście minut.

**Kolejne uruchomienie** (kopia i `android/` już są):

```powershell
Set-Location $env:USERPROFILE\p
npm.cmd run android
```

Po zmianach JS w gitowym `mobile/` zsynchronizuj źródła **bez** nadpisywania `android/`:

```powershell
cmd /c "robocopy `"C:\Users\kacpe\Documents\GitHub\PhysioCare\mobile`" `"$env:USERPROFILE\p`" /E /NFL /NDL /NJH /NJS /XD android node_modules .cxx .gradle"
```

Albo edytuj od razu w `C:\Users\kacpe\p` (git i tak commitujesz z repo).

### Po instalacji

1. Otwórz **PhysioCare** na telefonie (nie Expo Go).
2. Zaloguj pacjenta.
3. Zezwól na powiadomienia.
4. Z panelu terapeuty utwórz wizytę / dokument / ćwiczenie - na telefonie powinien przyjść **push** (przy `EMAIL_BACKEND=console` e-mail i tak wyleci tylko na konsolę Django).
5. Przypomnienia 24h/2h i „ćwiczenia na dziś” - drugi terminal: `python manage.py run_notification_scheduler` (cwd `backend/physiocare`).

---

## Skrypty

| Komenda                    | Opis                                    |
| -------------------------- | --------------------------------------- |
| `npm.cmd start`            | Metro + **dev client** (własny APK)     |
| `npm.cmd run start:go`     | Metro pod **Expo Go**                   |
| `npm.cmd run android`      | Native debug na urządzeniu / emulatorze |
| `npm.cmd run ios`          | Native iOS (macOS)                      |
| `npm.cmd run web`          | Przeglądarka                            |
| `npm.cmd run lint`         | ESLint + `tsc --noEmit`                 |
| `npm.cmd run lint:fix`     | Autofix ESLint                          |
| `npm.cmd run format`       | Prettier (write)                        |
| `npm.cmd run format:check` | Prettier (check)                        |

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
  notifications/    # push (pomijane w Expo Go)
  components/        # Button, Field, AsyncState, OfflineBanner…
  theme/             # tokeny kolorystyczne (olive clinic)
```

## Offline

- Globalny banner „Brak połączenia z internetem” (NetInfo)
- Wywołania API zwracają czytelny `NetworkError` zamiast crasha
- Przywracanie sesji offline: tokeny nie są kasowane; używany jest cache użytkownika
- Po powrocie sieci profil jest odświeżany automatycznie

## Powiadomienia push

Po zalogowaniu w **development build** aplikacja prosi o zgodę i wysyła token Expo. Wylogowanie deaktywuje token.

Android **wymaga FCM** (Expo Go ma to wbudowane, nasz APK nie):

1. [Firebase Console](https://console.firebase.google.com) → nowy projekt → Add app **Android**, package `com.physiocare.patient`.
2. Pobierz `google-services.json` do `mobile/` (i skopiuj do `%USERPROFILE%\p\`).
3. W `app.json` jest `android.googleServicesFile`.
4. Przebuduj native: z `C:\Users\kacpe\p` → `npm.cmd run android`.
5. Na [expo.dev](https://expo.dev) w projekcie PhysioCare → Credentials → wgraj FCM V1 (service account), wg [dokumentacji Expo](https://docs.expo.dev/push-notifications/fcm-credentials/).

Bez kroku 4 Metro JS nic nie zmieni - Firebase musi być w binarium.

## Reset hasła (deep link)

1. W appce: **Nie pamiętam hasła** → podaj e-mail → **Wyślij link** (backend wysyła mail z `physiocare://password-reset?token=…`).
2. Otwórz mail (Mailtrap / skrzynka) i kliknij link - OS powinien otworzyć PhysioCare na ekranie nowego hasła (hasło + powtórz).
3. Test bez maila (dev):

```bash
npx uri-scheme open "physiocare://password-reset?token=TEST_TOKEN" --android
```

Scheme jest w `app.json` (`physiocare`). Bez kliknięcia w link z maila nie ma jak ustawić hasła w UI.

## Status (Faza 5)

- **5.1** Szkielet Expo + tabs/stack
- **5.2** Auth + zgody RODO przy rejestracji
- **5.3** Pulpit + compliance ćwiczeń
- **5.4** Wizyty (nadchodzące / archiwum)
- **5.5** Profil, dokumenty, powiadomienia, zgody
- **5.6** Szczegóły wizyty + profil terapeuty
- **5.7** Integracja z API (Bearer JWT)
