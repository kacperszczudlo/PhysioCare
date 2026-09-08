# REST API — PhysioCare (kontrakt)

> Wersja dokumentu: **0.4**.  
> Kolekcja Postman: [`postman/PhysioCare.json`](postman/PhysioCare.json) · przewodnik: [`postman-testing.md`](postman-testing.md).

**Base URL:** `http://localhost:8000/api/v1`  
**Format:** JSON (`Content-Type: application/json`)  
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

### POST `/auth/logout`

Czyści cookies `access_token` / `refresh_token` i wpisuje przedstawiony refresh na czarną listę (body `refresh` albo cookie). **200** - `{ "detail": "Wylogowano." }`.

### POST `/auth/refresh`

```json
{ "refresh": "<refresh_token>" }
```

Cookie `refresh_token` też jest akceptowane (body opcjonalne).  
**200** - `{ "detail" }` + odświeżone cookies; gdy refresh przyszedł w JSON, odpowiedź zawiera też nową parę `access` / `refresh`. Stary refresh po rotacji jest na czarnej liście.
### POST `/auth/password-reset/request`

```json
{ "email": "..." }
```

### POST `/auth/password-reset/confirm`

```json
{ "token": "...", "new_password": "..." }
```

### POST `/auth/password-change`

Wymaga sesji. Body: `{ "current_password", "new_password" }`. **200** — hasło zmienione, sesje unieważnione; trzeba zalogować się ponownie.

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
| POST | `/me/account-deletion-request` | Wniosek o usunięcie (zapis + dezaktywacja konta) |

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
| GET/POST | `/episodes/{id}/device-orders` | THERAPIST | Zlecenia wyrobów (e-ZWM model) |
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

Odpowiedź: `{ count, results[] }` gdzie każdy element ma `id`, `kind`, `kind_label`, `title`, `summary`, `created_at`, `therapist_name`, `episode_id`, `status`, `file_url` (PDF), `details`. Wyroby i Recepta na Ruch tylko ze statusem `ISSUED`.

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

Domyślnie co 900 s (`NOTIFICATION_SCHEDULER_INTERVAL_SECONDS`). Jedna tura: `--once`. Deduplikacja w bazie — bezpieczne wielokrotne odpalenie. Nie wpinaj schedulera w workery Gunicorn (zdublowałby ticki).

Klucz `waitlist` jest w kontrakcie, ale w domenie nie ma jeszcze listy rezerwowej.

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
