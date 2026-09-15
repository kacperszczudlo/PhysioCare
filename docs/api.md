# REST API - PhysioCare (kontrakt)

> Wersja dokumentu: **0.5**.  
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
| Role | `PATIENT` \| `THERAPIST` - egzekwowane per endpoint |

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

Rejestracja z Google: w `POST /auth/register/therapist/` lub `/auth/register/patient/` wyślij `google_credential` zamiast `password` (e-mail/imię z tokenu). Web wymaga PWZFz (dla fizjoterapeuty); mobile - zgody RODO.

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
| GET | `/therapists/{id}/public` | Wizytówka dla pacjenta |

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

Domyślnie co 900 s (`NOTIFICATION_SCHEDULER_INTERVAL_SECONDS`). Jedna tura: `--once`. Deduplikacja w bazie - bezpieczne wielokrotne odpalenie. Nie wpinaj schedulera w workery Gunicorn (zdublowałby ticki).

Klucz `waitlist` jest w kontrakcie, ale w domenie nie ma jeszcze listy rezerwowej.

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
- Wiele workerów / instancji: bus między procesami (np. Redis) - szczegóły w [README - Na później (skalowanie)](../README.md#na-później-skalowanie).

Skalowanie multi-worker: [README - Na później](../README.md#na-później-skalowanie).

---

## Pliki

Upload: `multipart/form-data`, max rozmiar konfigurowalny w `.env` (`MAX_UPLOAD_MB`).

Dozwolone MIME: `application/pdf`, `video/mp4`.

---

## Kolejne kroki

1. ~~Implementacja serializers + permissions w DRF~~ (Faza 2)
2. ~~Eksport kolekcji Postman~~ -> [`postman/PhysioCare.json`](postman/PhysioCare.json), przewodnik [`postman-testing.md`](postman-testing.md)
3. Przejście checklisty Postman (wszystkie UC + wyjątki)
4. Walidacja kontraktu testami integracyjnymi (Faza 3)
5. ~~Realtime SSE (web + mobile)~~. Skalowanie N×M / Redis: README „Na później”.
