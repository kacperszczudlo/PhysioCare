# REST API - PhysioCare (kontrakt)

> Wersja dokumentu: **1.0 (Specyfikacja produkcyjna)**.  
> Kolekcja Postman: [`postman/PhysioCare.json`](postman/PhysioCare.json) · przewodnik: [`postman-testing.md`](postman-testing.md).

**Base URL:** `http://localhost:8000/api/v1`  
**Format:** JSON (`Content-Type: application/json`); wyjątek: stream realtime → `text/event-stream` (SSE), payload eventu nadal JSON.  
**Auth:** cookies `access_token` / `refresh_token` (httpOnly) **albo** `Authorization: Bearer <access_token>`.  
Login, rejestracja i refresh zwracają `access` + `refresh` w JSON, gdy klient nie wyśle `token_delivery: "cookie"` (tak działa mobile / SecureStore). Panel webowy prosi o dostawę cookie-only, żeby JWT nie lądował w ciele odpowiedzi.

## Konwencje

| Aspekt | Reguła |
|--------|--------|
| Identyfikatory | UUID v4 |
| Daty | ISO 8601 (`2026-06-09T14:30:00+02:00`) |
| Błędy | `{ "error": { "code": "...", "message": "...", "details": {} } }` |
| Paginacja | `?page=1&page_size=20` -> `{ "count", "next", "previous", "results" }` |
| Role | `PATIENT` \| `THERAPIST` \| `ADMIN` - egzekwowane per endpoint |

## Kody HTTP (wybrane)

| Kod | Zastosowanie |
|-----|--------------|
| 200 | GET/PATCH sukces |
| 201 | POST utworzenie |
| 204 | DELETE bez treści |
| 400 | Walidacja |
| 401 | Brak/nieprawidłowy token |
| 403 | Zła rola lub brak dostępu do zasobu |
| 404 | Nie znaleziono |
| 409 | Konflikt (np. kolizja terminu, duplikat e-mail) |
| 422 | Semantyka domenowa (np. brak wymaganej zgody) |

---

## Auth (`/auth/`)

### POST `/auth/register/patient`

```json
{
  "email": "pacjent@example.com",
  "password": "SecurePass123!",
  "first_name": "Jan",
  "last_name": "Kowalski",
  "therapist_id": "uuid-profilu-terapeuty",
  "consents": {
    "terms": true,
    "medical_data": true
  }
}
```

**201** - `{ "user": { "id", "email", "role", "first_name", "last_name" } }` + cookies JWT.  
`therapist_id` = UUID `TherapistProfile` (nie User).

### POST `/auth/register/therapist`

```json
{
  "email": "terapeuta@example.com",
  "password": "SecurePass123!",
  "first_name": "Anna",
  "last_name": "Nowak",
  "pwzf_number": "71239",
  "pwzf_declaration": true
}
```

### POST `/auth/login`

```json
{ "email": "...", "password": "..." }
```

**200** - `{ "user": {...}, "access": "<jwt>", "refresh": "<jwt>" }` + cookies JWT.  
Mobile zapisuje `access`/`refresh` (np. SecureStore) i wysyła `Authorization: Bearer`.

Konta tylko-Google (bez lokalnego hasła) dostają **401** `AUTH_023` z komunikatem, żeby użyć przycisku Google.

### POST `/auth/google`

Wymiana Google ID token (GIS / Sign in with Google) na sesję PhysioCare.

```json
{ "credential": "<google_id_token>", "token_delivery": "cookie" }
```

`credential` albo `id_token`. `token_delivery: "cookie"` jak przy loginie webowym; mobile pomija → tokeny w body.

Wymaga `GOOGLE_CLIENT_IDS` (lista audience). Serwer weryfikuje token (`google-auth`), potem:

1. użytkownik po `google_sub`, albo
2. istniejący e-mail → powiązanie `google_sub`, albo
3. **404** `AUTH_025` - brak konta (najpierw rejestracja z PWZFz / terapeutą).

**200** - jak `/auth/login`. Bez konfiguracji Google: **503** `AUTH_020`.

### GET / PATCH `/auth/me/`

Zwraca lub częściowo aktualizuje dane zalogowanego użytkownika (imię, nazwisko). Dostępne dla każdej roli (`PATIENT`, `THERAPIST`, `ADMIN`).

- **GET**: Zwraca `{ "user": { "id", "email", "role", "first_name", "last_name" } }`.
- **PATCH**: Przyjmuje opcjonalne pola `{ "first_name": "...", "last_name": "..." }`, waliduje reguły i zwraca zaktualizowany obiekt `{ "user": { ... } }`.

### POST `/auth/logout`

Czyści cookies `access_token` / `refresh_token` i wpisuje przedstawiony refresh na czarną listę (body `refresh` albo cookie). **200** - `{ "detail": "Wylogowano." }`.

### 2FA / MFA (Dwuskładnikowa autentykacja TOTP)

Służy do dodania drugiego składnika autentykacji dla ról o podwyższonym poziomie dostępu (np. fizjoterapeuci, admini).

#### 1. Dwuetapowe logowanie gdy 2FA jest włączone

Wywołanie `POST /auth/login/` przy aktywnym 2FA zwraca:
**200** - `{ "mfa_required": true, "mfa_token": "<podpisany_token_preauth>", "email": "..." }`

Następnie klient przekazuje `mfa_token` oraz `code` w **Kroku 2**:

#### POST `/auth/2fa/login`
```json
{
  "mfa_token": "<podpisany_token_preauth>",
  "code": "123456"
}
```
* `code` może być 6-cyfrowym kodem z aplikacji Google Authenticator **lub** 8-znakowym jednorazowym kodem ratunkowym (backup code).

**200** - zwraca tokeny sesyjne sesji JWT (`user`, `access`, `refresh`).  
**401** `AUTH_MFA_TOKEN_INVALID` - token preauth wygasł (TTL 5 minut) lub jest nieprawidłowy.  
**401** `AUTH_MFA_INVALID_CODE` - nieprawidłowy kod 2FA lub użyty/błędny kod zapasowy.

#### POST `/auth/2fa/setup` (wymaga auth)
Inicjalizuje konfigurację 2FA dla zalogowanego użytkownika. Zwraca tajny klucz Base32, URI `otpauth://...` oraz wektorowy kod QR (XML SVG).

**200**:
```json
{
  "secret_key": "JBSWY3DPEHPK3PXP",
  "otpauth_url": "otpauth://totp/PhysioCare:user@example.com?secret=JBSWY3DPEHPK3PXP&issuer=PhysioCare",
  "qr_code_svg": "<svg ...></svg>"
}
```

#### POST `/auth/2fa/enable` (wymaga auth)
Aktywuje 2FA po podaniu pierwszego poprawnego kodu TOTP. Zwraca 8 jednorazowych kodów zapasowych.

```json
{
  "code": "123456"
}
```

**200**:
```json
{
  "message": "Dwuskładnikowa autentykacja została pomyślnie aktywowana.",
  "backup_codes": ["A1B2-C3D4", "E5F6-G7H8", "..."]
}
```

#### POST `/auth/2fa/disable` (wymaga auth)
Wyłącza dwuskładnikową autentykację na koncie. Wymaga podania aktualnego hasła.

```json
{
  "password": "SecurePass123!",
  "code": "123456"
}
```

**200** - `{ "message": "Dwuskładnikowa autentykacja została wyłączona." }`

#### GET `/auth/2fa/status` (wymaga auth)
Zwraca obecny status 2FA użytkownika oraz flagę wymogu dla jego roli.

**200**:
```json
{
  "is_enabled": true,
  "mfa_required_for_role": true
}
```



### POST `/auth/refresh`

```json
{ "refresh": "<refresh_token>" }
```

Cookie `refresh_token` też jest akceptowane (body opcjonalne).  
**200** - `{ "detail" }` + odświeżone cookies; gdy refresh przyszedł w JSON, odpowiedź zawiera też nową parę `access` / `refresh`. Stary refresh po rotacji jest na czarnej liście.
### POST `/auth/password-reset/request`

```json
{ "email": "...", "client": "web" }
```

`client` opcjonalne (`web` / `mobile`) - tylko dla logów/diagnostyki. Na e-mail idzie **6-cyfrowy kod** (TTL: `PASSWORD_RESET_TIMEOUT`).

**200** - `{ "detail": "Wysłaliśmy 6-cyfrowy kod…" }`  
**404** `AUTH_029` - brak konta z tym e-mailem.  
**400** `AUTH_023` - konto tylko-Google (bez lokalnego hasła).  
**503** `AUTH_030` - błąd wysyłki SMTP.

### POST `/auth/password-reset/verify`

```json
{ "email": "...", "code": "123456" }
```

Sprawdza kod z e-maila. Po sukcesie kod jest zużyty; klient dostaje krótkotrwały `reset_token` do ustawienia hasła.

**200** - `{ "detail": "Kod jest poprawny…", "reset_token": "..." }`  
**400** `AUTH_028` - zły / wygasły kod lub przekroczony limit prób.

### POST `/auth/password-reset/confirm`

```json
{
  "reset_token": "...",
  "new_password": "...",
  "new_password_confirm": "..."
}
```

Po sukcesie hasło zmienione, sesje unieważnione. Niezweryfikowany e-mail zostaje oznaczony jako zweryfikowany.  
**400** `AUTH_028` - wygasła / zużyta sesja resetu (`reset_token`).

### POST `/auth/email/verify`

```json
{ "email": "...", "code": "123456", "token_delivery": "cookie" }
```

Potwierdza adres po rejestracji e-mail+hasło. **200** - sesja jak przy loginie. Konta Google pomijają ten krok (`email_verified_at` ustawiane od razu).

### GET `/auth/me`

Zwraca profil aktualnie uwierzytelnionego użytkownika dla wszystkich ról (`PATIENT`, `THERAPIST`, `ADMIN`), umożliwiając odtworzenie sesji oraz dynamiczne trasowanie RBAC w warstwie klienta.

**Wymaga:** Auth (cookie `access_token` lub nagłówek `Authorization: Bearer <token>`).

**200 OK:**
```json
{
  "id": "c1f79a95-5fa8-4bf3-a3d2-d17e305e7e39",
  "email": "admin@physiocare.pl",
  "first_name": "Aleksandra",
  "last_name": "Nowak",
  "role": "ADMIN",
  "email_verified": true,
  "is_active": true,
  "has_mfa": true,
  "google_linked": false,
  "created_at": "2026-03-01T10:00:00Z"
}
```
**401 Unauthorized:** Brak sesji lub token wygasł.

### POST `/auth/email/resend`

```json
{ "email": "..." }
```

Ponowny kod weryfikacyjny (anti-enumeration).

Rejestracja patient/therapist **bez** Google zwraca **201**:

```json
{ "needs_email_verification": true, "email": "...", "detail": "..." }
```

bez JWT. Logowanie hasłem przy braku weryfikacji: **403** `AUTH_027`.

### POST `/auth/password-change`

Wymaga sesji. Body: `{ "current_password", "new_password" }`. **200** - hasło zmienione, sesje unieważnione; trzeba zalogować się ponownie.

---

## Pacjent - profil (`/me/`)

| Metoda | Endpoint | Opis |
|--------|----------|------|
| GET | `/me/profile` | Dane pacjenta |
| PATCH | `/me/profile` | Edycja PESEL, telefon |
| POST | `/me/profile/avatar` | Upload avatara (`multipart`, pole `file`: JPEG/PNG/WebP) |
| GET | `/me/therapists` | Lista powiązanych fizjoterapeutów pacjenta (UC-20) |
| POST | `/me/therapists/link` | Powiązanie fizjoterapeuty (`{ "therapist_id": "uuid" }`) |
| DELETE | `/me/therapists/{id}` | Usunięcie powiązania z fizjoterapeutą |
| GET | `/me/consents` | Lista zgód |
| PATCH | `/me/consents/optional` | Marketing, badania |
| POST | `/me/data-export` | Eksport RODO (profil, zgody, wizyty, epizody, dokumenty, ćwiczenia, preferencje i logi powiadomień) |
| POST | `/me/account-deletion-request` | Wniosek o usunięcie: opcjonalne `reason`, dezaktywacja tokenów push, anonimizacja PII (e-mail zwolniony do ponownej rejestracji), unieważnienie sesji |

---

## Wizyty (`/visits/`)

| Metoda | Endpoint | Rola | Opis |
|--------|----------|------|------|
| GET | `/me/visits?status=upcoming` | PATIENT | Nadchodzące |
| GET | `/me/visits?status=past` | PATIENT | Archiwum |
| GET | `/visits/{id}` | obie | Szczegóły |
| PATCH | `/visits/{id}/reschedule` | PATIENT | Zmiana terminu |
| POST | `/visits/{id}/cancel` | obie | Odwołanie + powód |
| GET | `/therapist/visits?date=2026-06-09` | THERAPIST | Harmonogram dnia |
| GET | `/therapist/visits?upcoming=1` | THERAPIST | Najbliższe zaplanowane (od teraz) |
| POST | `/therapist/visits` | THERAPIST | Nowa wizyta |
| PATCH | `/therapist/visits/{id}` | THERAPIST | Edycja / drag slot |
| POST | `/therapist/visits/{id}/approve` | THERAPIST | Zatwierdzenie prośby o wizytę (`PENDING_APPROVAL`) |
| POST | `/therapist/visits/{id}/reject` | THERAPIST | Odrzucenie prośby o wizytę (`PENDING_APPROVAL`) |
| GET | `/therapist/availabilities/` | THERAPIST | Lista slotów dostępności terapeuty |
| POST | `/therapist/availabilities/` | THERAPIST | Utworzenie nowego slotu pracy (cykliczny/jednorazowy) |
| DELETE | `/therapist/availabilities/{id}` | THERAPIST | Usunięcie slotu dostępności |
| GET | `/therapists/{id}/available-slots/` | obie | Publiczne wolne sloty terapeuty na dany dzień (`?date=YYYY-MM-DD`) |

**Przykład tworzenia wizyty (terapeuta):**

```json
{
  "patient_id": "uuid",
  "episode_id": "uuid",
  "therapy_type_id": "uuid",
  "start_at": "2026-06-10T11:00:00+02:00",
  "end_at": "2026-06-10T11:45:00+02:00",
  "location_address": "ul. Przykładowa 1, Tarnów",
  "prep_instructions": "Proszę zabrać aktualne wyniki badań."
}
```

---

## Epizody i diagnoza (`/episodes/`)

| Metoda | Endpoint | Rola | Opis |
|--------|----------|------|------|
| GET | `/patients/{id}/episodes` | THERAPIST | Lista epizodów |
| POST | `/patients/{id}/episodes` | THERAPIST | Nowy epizod |
| PATCH | `/episodes/{id}` | THERAPIST | Status, ICD-10 |
| GET | `/episodes/{id}/body-pain` | THERAPIST | Wpisy mapy ciała |
| POST | `/episodes/{id}/body-pain` | THERAPIST | Nowy wpis VAS |
| PUT/PATCH | `/episodes/{id}/body-pain/{entry_id}` | THERAPIST | Aktualizacja |
| DELETE | `/episodes/{id}/body-pain/{entry_id}` | THERAPIST | Usunięcie wpisu |
| POST | `/episodes/{id}/notes` | THERAPIST | Notatka z wizyty |
| GET | `/episodes/{id}/notes` | THERAPIST | Lista notatek epizodu |
| GET/POST | `/episodes/{id}/diagnostic-recommendations` | THERAPIST | Kierowanie pośrednie (opinia) |
| PATCH/DELETE | `/episodes/{id}/diagnostic-recommendations/{item_id}` | THERAPIST | Edycja / usunięcie kierowania |
| GET/POST | `/episodes/{id}/device-orders` | THERAPIST | Zlecenia wyrobów (e-ZWM model); opcjonalny `access_code` (4 cyfry z NFZ) |
| PATCH/DELETE | `/episodes/{id}/device-orders/{item_id}` | THERAPIST | Edycja / usunięcie zlecenia |
| GET/POST | `/episodes/{id}/order-refusals` | THERAPIST | Odmowa zlecenia lekarskiego |
| PATCH/DELETE | `/episodes/{id}/order-refusals/{item_id}` | THERAPIST | Edycja / usunięcie odmowy |
| GET/POST | `/patients/{id}/recepta-na-ruch` | THERAPIST | Skierowanie Recepta na Ruch |
| PATCH/DELETE | `/patients/{id}/recepta-na-ruch/{item_id}` | THERAPIST | Edycja / usunięcie skierowania |
| GET | `/medical-devices/catalog` | THERAPIST | Katalog wyrobów + kompetencje |
| GET | `/me/clinical-documents` | PATIENT | Skrzynka dokumentacji pacjenta |

**Dokumentacja pacjenta** (`GET /me/clinical-documents`):

Wystawienie przez terapeutę udostępnia wpis pacjentowi automatycznie (bez osobnego uploadu).

| Param | Znaczenie |
|-------|-----------|
| `kind` | Opcjonalnie: `recommendation` \| `device_order` \| `refusal` \| `recepta_na_ruch` \| `pdf` |

Odpowiedź: `{ count, results[] }` gdzie każdy element ma `id`, `kind`, `kind_label`, `title`, `summary`, `created_at`, `therapist_name`, `episode_id`, `status`, `file_url` (PDF), `details`. Wyroby i Recepta na Ruch tylko ze statusem `ISSUED`. Podsumowania wizyt (`patient_summary`) są wyłącznie na karcie wizyty, nie w tej skrzynce.

**Body pain:**

```json
{
  "body_region": "right-quadriceps",
  "view_side": "FRONT",
  "vas_score": 7,
  "pain_character": ["SHARP", "RADIATING"],
  "treatment_targets": ["QUAD_R", "HIP_JT_R"]
}
```

`body_region` - slug mięśnia/regionu z modelu anatomicznego (np. `left-lower-back`, `right-quadriceps`).  
`treatment_targets` - opcjonalne cele leczenia (staw / mięsień / kość / tkanka) dla wybranego regionu.

---

## Ćwiczenia (`/exercises/`)

| Metoda | Endpoint | Rola | Opis |
|--------|----------|------|------|
| GET | `/therapist/exercises` | THERAPIST | Katalog - filtry poniżej; paginacja `?page=` (domyślnie 20) |
| GET | `/therapist/exercises/{id}` | THERAPIST | Szczegóły ćwiczenia |
| GET | `/therapist/exercise-categories` | THERAPIST | Lista kategorii (`?kind=TYPE\|REGION\|MUSCLE\|INJURY`) |
| POST | `/therapist/exercises` | THERAPIST | Upload metadanych + plik |
| PATCH | `/therapist/exercises/{id}` | THERAPIST | Edycja (plik opcjonalny) |
| DELETE | `/therapist/exercises/{id}` | THERAPIST | Usunięcie (kaskada: przypisania) |
| GET | `/therapist/exercise-assignments` | THERAPIST | Lista (`?patient=`, `?active=1`) |
| POST | `/therapist/exercise-assignments` | THERAPIST | Przypisanie |
| PATCH | `/therapist/exercise-assignments/{id}` | THERAPIST | Okres / dawkowanie |
| DELETE | `/therapist/exercise-assignments/{id}` | THERAPIST | Usunięcie zalecenia |
| GET | `/me/exercises/today` | PATIENT | Zalecenia na dziś |
| POST | `/me/exercise-completions` | PATIENT | Oznacz / odznacz wykonanie (`done: true\|false`) |

**Filtry katalogu** (`GET /therapist/exercises`):

| Param | Znaczenie |
|-------|-----------|
| `type` | Typ ćwiczenia - slug lub UUID (`strengthening`, `stretching`, `mobilization`, `education`…) |
| `region` | Okolica ciała (`knee`, `lumbar`, `shoulder`…) |
| `muscle` | Mięsień / grupa (`quadriceps`, `gluteals`…) |
| `injury` | Kontuzja / wskazanie (`acl_rehab`, `lbp`…) |
| `category` | Dowolna kategoria (slug lub UUID); OR przy wielu wartościach |
| `media_type` | `VIDEO` / `PDF` |
| `q` | Szukaj w tytule i instrukcji |

Wymiary `type` / `region` / `muscle` / `injury` łączone są **AND** (ćwiczenie musi mieć tag z każdego wybranego wymiaru). W ramach jednego parametru wiele wartości (powtórzony query lub CSV) to **OR**.

**Kategoria w odpowiedzi:** `{ id, name, kind, slug }` gdzie `kind` ∈ `TYPE` | `REGION` | `MUSCLE` | `INJURY`.

**Przypisanie:**

```json
{
  "exercise_id": "uuid",
  "patient_id": "uuid",
  "episode_id": "uuid",
  "dosage": "3 serie x 10 powt.",
  "start_date": "2026-06-09",
  "end_date": "2026-06-23"
}
```

---

## Dokumenty (`/documents/`)

| Metoda | Endpoint | Opis |
|--------|----------|------|
| GET | `/me/documents` | Lista samych PDF pacjenta (legacy / wąski widok) |
| GET | `/me/clinical-documents` | Pełna skrzynka: kierowanie, wyroby, odmowy, Recepta na Ruch + PDF (`file_url` dla PDF = `/api/v1/{id}/download/`) |
| GET | `/{id}/download` | Pobranie (auth + ownership) |
| GET | `/media/<path>` | Serwowanie plików (JWT + ownership; dokumenty/ćwiczenia/avatary) |
| POST | `/therapist/documents` | Upload PDF przez terapeutę (`multipart`) |

---

## Terapeuta - profil i statystyki

| Metoda | Endpoint | Opis |
|--------|----------|------|
| GET | `/therapist/profile` | Biogram, kursy, PWZFz, avatar |
| PATCH | `/therapist/profile` | Edycja (telefon, bio, kursy) |
| POST | `/therapist/profile/avatar` | Upload avatara (`multipart`, pole `file`: JPEG/PNG/WebP) |
| GET | `/therapist/dashboard/stats` | Widgety pulpitu |
| GET | `/therapists/public` | Lista publicznych wizytówek fizjoterapeutów (`?search=...`) |
| GET | `/therapists/{id}/public` | Wizytówka pojedynczego fizjoterapeuty dla pacjenta |

---

## Powiadomienia

| Metoda | Endpoint | Opis |
|--------|----------|------|
| GET | `/me/notification-preferences` | Preferencje (kanoniczne klucze; brakujące są dosiewane jako włączone) |
| PATCH | `/me/notification-preferences` | Aktualizacja switchy |

Kanoniczne `pref_key`: `visit_reminder`, `visit_change`, `waitlist`, `exercise_reminder`, `new_document`.

PATCH przyjmuje płaską mapę `{ "visit_reminder": false }` albo `{ "preferences": { ... } }`. Nieznane klucze zwracają `400`.

| Metoda | Endpoint | Opis |
|--------|----------|------|
| GET | `/me/device-tokens` | Aktywne tokeny Expo pacjenta |
| POST | `/me/device-tokens` | Rejestracja / odświeżenie tokenu (`expo_push_token`, opcjonalnie `platform`: `ios` / `android` / `unknown`) |
| DELETE | `/me/device-tokens` | Dezaktywacja tokenu (body: `expo_push_token`) |

Wysyłka: zdarzenia domenowe (`visit_change`, `new_document`, nowe przypisanie ćwiczeń) idą od razu. Push Expo, gdy jest aktywny token; w przeciwnym razie e-mail.

Przypomnienia `visit_reminder` (okna 24h i 2h, ±30 min) oraz `exercise_reminder` (raz dziennie, pierwsza tura po północy) odpala **osobny proces**:

`python manage.py run_notification_scheduler`

Deduplikacja w bazie zapewnia bezpieczne wielokrotne uruchomienie schedulera. Usługa harmonogramu uruchamiana jest jako niezależny proces w tle.

---

## Realtime - SSE (`/me/events/`)

Live odświeżanie UI (bez F5 / bez zmiany zakładki). **Nie zastępuje** push Expo ani e-mail - te kanały zostają na tło / zamkniętą apkę.

### GET `/me/events/`

| | |
|--|--|
| Auth | Wymagany: cookie **lub** `Authorization: Bearer` (jak reszta `/me/`) |
| Role | `THERAPIST` \| `PATIENT` |
| Accept | `text/event-stream` (EventSource / klient SSE; inaczej DRF → 406) |
| Odpowiedź | `200` + `Content-Type: text/event-stream` (długie połączenie) |
| Cel | Sygnał „zmieniło się X” → klient robi **refetch** istniejącego REST (invalidate + reload) |

Klient utrzymuje jedno połączenie na sesję (po zalogowaniu). Po utracie sieci / wygaśnięciu access: refresh tokenu → ponowne `GET /me/events/`.

#### Format ramki SSE

```
event: <type>
data: {"type":"<type>","resource_id":"<uuid|null>","at":"<ISO8601>"}

```

- `event` i pole `type` w JSON są zawsze takie same.
- `resource_id`: UUID zasobu domenowego albo `null` (np. `ping`).
- Brak pełnego stanu kalendarza / list w streamie - tylko sygnał.

#### Typy eventów (v1)

| `type` | Kiedy | Odbiorcy | Co refetchuje klient |
|--------|--------|----------|----------------------|
| `visit.scheduled` | Utworzenie wizyty / prośba o termin | Terapeuta wizyty + pacjent | Web: Harmonogram, Pulpit · Mobile: Wizyty, Pulpit |
| `visit.rescheduled` | Zmiana terminu | j.w. | j.w. |
| `visit.cancelled` | Odwołanie | j.w. | j.w. |
| `visit.approved` | Zatwierdzenie pending | j.w. | j.w. |
| `visit.rejected` | Odrzucenie pending | j.w. | j.w. |
| `document.created` | Nowy PDF lub pozycja skrzynki klinicznej (kierowanie, wyrób ISSUED, odmowa, Recepta ISSUED) | Pacjent-właściciel | Mobile: Dokumenty |
| `exercise.assigned` | Nowe przypisanie ćwiczenia | Pacjent | Mobile: Pulpit („Zalecenia na dziś”) |
| `ping` | Heartbeat serwera (ok. co 15-30 s) | Abonent streamu | Nic (utrzymanie połączenia) |

Przykład `data` dla wizyty:

```json
{
  "type": "visit.cancelled",
  "resource_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "at": "2026-09-08T21:15:00+02:00"
}
```

Przykład `ping`:

```json
{
  "type": "ping",
  "resource_id": null,
  "at": "2026-09-08T21:15:30+02:00"
}
```

#### Zasady dostarczania

- Publikacja **per `user_id`** (tylko zainteresowani użytkownicy danej wizyty / dokumentu / przypisania) - nie broadcast całej kliniki.
- Wizyty: SSE zawsze do **pacjenta i terapeuty** wizyty (`publish_visit_realtime`). Push/e-mail do pacjenta nadal tylko przez `notify_visit_change` (np. prośba pacjenta o termin = SSE bez maila do siebie).
- Emit przy mutacjach domenowych (create/approve/reject/reschedule/cancel wizyty, upload PDF, przypisanie ćwiczenia).
- Preferencje powiadomień (`visit_change` itd.) **nie wyciszają** SSE - SSE to synchronizacja otwartego UI, nie kanał marketingowy.
- Błędy auth na starcie streamu: `401` / `403` jak w REST (bez otwarcia streamu).

#### Uwagi wdrożeniowe (kontrakt vs runtime)

- Demo / lokalnie: ASGI (np. uvicorn). Sync Gunicorn + wiele równoległych streamów = słabe dopasowanie.
- Wiele workerów / instancji: bus między procesami (np. Redis) - szczegóły w [README - Skalowanie i Architektura Realtime (SSE)](../README.md#skalowanie-i-architektura-realtime-sse).

---

## Panel Administracyjny (`/admin/`)

Wszystkie endpointy w tej sekcji wymagają uwierzytelnienia sesyjnego oraz roli **`ADMIN`** (egzekwowane przez klasę uprawnień `IsAdminRole`). Próba wywołania przez pacjenta lub fizjoterapeutę zwraca **403 Forbidden**.

### GET `/admin/dashboard/`

Zwraca zagregowane wskaźniki KPI dla głównego pulpitu analitycznego kliniki:
- Rozbicie bazy użytkowników (`total`, `patients_count` [App], `therapists_count` [Web], `admins_count`, `active_count`, `inactive_count`, `new_last_30_days`).
- Statystyki wizyt (`total`, `scheduled`, `completed`, `cancelled`, `no_show`, `pending_approval`, `show_up_rate_percent`).
- Metryki satysfakcji pacjentów (`rating_avg`, `rating_count`).
- Baza ćwiczeń i programów (`total_exercises`, `total_assignments`).

**200 OK:**
```json
{
  "users": {
    "total": 142,
    "patients_count": 120,
    "therapists_count": 20,
    "admins_count": 2,
    "active_count": 139,
    "inactive_count": 3,
    "new_last_30_days": 15
  },
  "visits": {
    "total": 350,
    "scheduled": 45,
    "completed": 280,
    "cancelled": 15,
    "no_show": 10,
    "pending_approval": 0,
    "show_up_rate_percent": 92.5
  },
  "quality": {
    "rating_avg": 4.88,
    "rating_count": 75
  },
  "exercises": {
    "total_exercises": 84,
    "total_assignments": 210
  }
}
```

### GET `/admin/users/`

Paginowana lista użytkowników systemu z możliwością filtrowania i wyszukiwania.

**Parametry zapytania (query params):**
- `search` – filtr tekstowy przeszukujący imię, nazwisko oraz adres e-mail.
- `role` – filtr roli: `PATIENT` | `THERAPIST` | `ADMIN`.
- `is_active` – filtr statusu konta: `true` | `false`.
- `email_verified` – filtr weryfikacji adresu e-mail: `true` | `false`.
- `page` – numer strony (domyślnie 1, rozmiar strony 20).

**200 OK:**
```json
{
  "count": 142,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": "e9b1c2d3-...",
      "email": "piotr@example.com",
      "first_name": "Piotr",
      "last_name": "Zieliński",
      "role": "PATIENT",
      "is_active": true,
      "email_verified": true,
      "created_at": "2026-03-01T10:00:00Z",
      "last_login": "2026-03-05T12:30:00Z"
    }
  ]
}
```

### GET `/admin/users/{id}/`

Zwraca szczegółowy profil użytkownika wraz z metadanymi roli (numer PWZF, stopień kwalifikacji dla fizjoterapeuty, telefon, liczba zrealizowanych wizyt, status 2FA i powiązanie z Google).

**200 OK:**
```json
{
  "id": "e9b1c2d3-...",
  "email": "piotr@example.com",
  "first_name": "Piotr",
  "last_name": "Zieliński",
  "role": "PATIENT",
  "is_active": true,
  "email_verified": true,
  "has_mfa": false,
  "google_linked": true,
  "created_at": "2026-03-01T10:00:00Z",
  "visits_count": 4,
  "profile_info": {
    "phone": "+48 500 600 700"
  }
}
```

### PATCH `/admin/users/{id}/status/`

Blokuje lub odblokowuje konto użytkownika (`is_active`). Przy zablokowaniu konta następuje unieważnienie wszystkich aktywnych tokenów odświeżających (JWT Blacklist).

```json
{
  "is_active": false
}
```

**200 OK:** Zwraca zaktualizowany obiekt szczegółów użytkownika.  
**403 Forbidden:** Administrator nie może zablokować własnego konta.

### POST `/admin/users/{id}/reset-password/`

Inicjuje wysyłkę 6-cyfrowego kodu resetowania hasła na powiązany adres e-mail użytkownika.

**200 OK:**
```json
{
  "message": "Kod resetu hasła został wysłany na adres uzytkownik@example.com."
}
```
**400 Bad Request:** Nie można zresetować hasła zablokowanego konta (`is_active=False`).

### DELETE `/admin/users/{id}/`

Bezpieczna dezaktywacja konta użytkownika (soft-delete RODO). Wyłącza konto (`is_active=False`), unieważnia tokeny sesyjne oraz zabezpiecza integralność medyczną bazy danych (brak kaskadowego usuwania historii wizyt).

**200 OK:**
```json
{
  "message": "Użytkownik został pomyślnie zdezaktywowany."
}
```
**403 Forbidden:** Administrator nie może usunąć własnego konta.

### GET `/admin/schedules/overview/`

Wielostanowiskowy przegląd harmonogramu pracy i wizyt personelu medycznego w zadanym oknie czasowym.

**Parametry zapytania:**
- `date_from` – początek okna czasowego (ISO 8601).
- `date_to` – koniec okna czasowego (ISO 8601).
- `therapist_id` – opcjonalny UUID fizjoterapeuty do filtrowania.

**200 OK:**
```json
{
  "range": {
    "start_at": "2026-03-01T00:00:00Z",
    "end_at": "2026-03-08T23:59:59Z"
  },
  "therapists": [
    {
      "id": "uuid-profilu-terapeuty",
      "user_id": "uuid-usera",
      "name": "Tomasz Nowak",
      "email": "tomasz@physiocare.pl",
      "qualification_level": "Specjalista",
      "rating_avg": 4.9,
      "rating_count": 10
    }
  ],
  "visits": [
    {
      "id": "uuid-wizyty",
      "patient_id": "uuid-pacjenta",
      "patient_name": "Michał Wiśniewski",
      "therapist_id": "uuid-terapeuty",
      "therapist_name": "Tomasz Nowak",
      "therapy_type_name": "Rehabilitacja pourazowa",
      "therapy_type_color": "#3b82f6",
      "start_at": "2026-03-02T10:00:00Z",
      "end_at": "2026-03-02T11:00:00Z",
      "status": "SCHEDULED",
      "location_address": "Gabinet 102"
    }
  ],
  "availability_slots": [
    {
      "id": "uuid-slotu",
      "therapist_id": "uuid-terapeuty",
      "therapist_name": "Tomasz Nowak",
      "day_of_week": 1,
      "start_time": "08:00:00",
      "end_time": "16:00:00",
      "is_active": true
    }
  ]
}
```

### GET `/admin/therapists/stats/`

Zestawienie efektywności personelu: numer PWZF, poziom kwalifikacji, lata stażu, liczba ukończonych/odwołanych/nieodbytych wizyt (no-show) oraz średnia ocen i liczba opinii.

**200 OK:**
```json
[
  {
    "therapist_id": "uuid-profilu",
    "user_id": "uuid-usera",
    "first_name": "Tomasz",
    "last_name": "Nowak",
    "email": "tomasz@physiocare.pl",
    "pwzf_number": "71239",
    "qualification_level": "Magister Fizjoterapii",
    "experience_years": 8,
    "rating_avg": 4.95,
    "rating_count": 42,
    "total_visits": 120,
    "completed_visits": 110,
    "cancelled_visits": 7,
    "no_show_visits": 3,
    "pending_visits": 0
  }
]
```

### GET `/admin/reviews/`

Paginowana lista recenzji pacjentów do moderacji.

**Parametry zapytania:**
- `rating` – ocena gwiazdkowa (1–5).
- `is_visible` – status widoczności (`true` | `false`).
- `therapist_id` – identyfikator ocenianego fizjoterapeuty.

**200 OK:**
```json
{
  "count": 45,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": "uuid-opinii",
      "patient_id": "uuid-pacjenta",
      "patient_name": "Anna Kowalska",
      "therapist_id": "uuid-terapeuty",
      "therapist_name": "Tomasz Nowak",
      "rating": 5,
      "comment": "Znakomity specjalista, terapia przyniosła natychmiastową ulgę.",
      "is_anonymous": false,
      "is_visible": true,
      "therapist_reply": "Dziękuję za miłe słowa!",
      "therapist_replied_at": "2026-03-02T10:00:00Z",
      "created_at": "2026-03-01T15:30:00Z"
    }
  ]
}
```

### PATCH `/admin/reviews/{id}/visibility/`

Ukrywa opinię (zmoderowana przez administratora) lub przywraca jej widoczność publiczną. Zmiana statusu widoczności automatycznie uruchamia sygnał rekalkulacji średniej ocen i liczby recenzji ocenianego fizjoterapeuty.

```json
{
  "is_visible": false
}
```

**200 OK:** Zwraca zaktualizowaną recenzję z nowym statusem `is_visible`.

---

## Pliki

Upload: `multipart/form-data`, max rozmiar konfigurowalny w `.env` (`MAX_UPLOAD_MB`).

Dozwolone MIME: `application/pdf`, `video/mp4`.

---

## Stan i weryfikacja kontraktu

Kontrakt REST API oraz Realtime SSE zostały w pełni zaimplementowane. Weryfikacja spójności odbywa się poprzez:
1. Kolekcję Postman: [`postman/PhysioCare.json`](postman/PhysioCare.json) (przewodnik [`postman-testing.md`](postman-testing.md)).
2. Zintegrowany pakiet testów automatycznych `pytest` (`backend/tests/`).
3. Zsynchronizowany skrypt weryfikacyjny: `python scripts/run_postman.py`.
