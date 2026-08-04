# REST API — PhysioCare (szkic kontraktu)

> Wersja dokumentu: **0.3 (Faza 2 — implementacja)**.  
> Kolekcja Postman: [`postman/PhysioCare.json`](postman/PhysioCare.json) · przewodnik testów: [`postman-testing.md`](postman-testing.md).

**Base URL:** `http://localhost:8000/api/v1`  
**Format:** JSON (`Content-Type: application/json`)  
**Auth:** cookies `access_token` / `refresh_token` (httpOnly) **lub** `Authorization: Bearer <access_token>`

## Konwencje

| Aspekt | Reguła |
|--------|--------|
| Identyfikatory | UUID v4 |
| Daty | ISO 8601 (`2026-06-09T14:30:00+02:00`) |
| Błędy | `{ "error": { "code": "...", "message": "...", "details": {} } }` |
| Paginacja | `?page=1&page_size=20` → `{ "count", "next", "previous", "results" }` |
| Role | `PATIENT` \| `THERAPIST` — egzekwowane per endpoint |

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

**201** — `{ "user": { "id", "email", "role", "first_name", "last_name" } }` + cookies JWT.  
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

### POST `/auth/refresh`

```json
{ "refresh": "<refresh_token>" }
```

### POST `/auth/password-reset/request`

```json
{ "email": "..." }
```

### POST `/auth/password-reset/confirm`

```json
{ "token": "...", "new_password": "..." }
```

---

## Pacjent — profil (`/me/`)

| Metoda | Endpoint | Opis |
|--------|----------|------|
| GET | `/me/profile` | Dane pacjenta |
| PATCH | `/me/profile` | Edycja PESEL, telefon, avatar |
| GET | `/me/consents` | Lista zgód |
| PATCH | `/me/consents/optional` | Marketing, badania |
| POST | `/me/data-export` | Eksport RODO |
| POST | `/me/account-deletion-request` | Wniosek o usunięcie |

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
| PUT | `/episodes/{id}/body-pain/{entry_id}` | THERAPIST | Aktualizacja |
| POST | `/episodes/{id}/notes` | THERAPIST | Notatka z wizyty |

**Body pain:**

```json
{
  "body_region": "THIGH_RIGHT",
  "view_side": "FRONT",
  "vas_score": 7,
  "pain_character": ["SHARP", "RADIATING"]
}
```

---

## Ćwiczenia (`/exercises/`)

| Metoda | Endpoint | Rola | Opis |
|--------|----------|------|------|
| GET | `/therapist/exercises` | THERAPIST | Katalog + filtry |
| POST | `/therapist/exercises` | THERAPIST | Upload metadanych + plik |
| POST | `/therapist/exercise-assignments` | THERAPIST | Przypisanie |
| GET | `/me/exercises/today` | PATIENT | Zalecenia na dziś |
| POST | `/me/exercise-completions` | PATIENT | Oznacz wykonanie |

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
| GET | `/me/documents` | Lista PDF pacjenta |
| GET | `/{id}/download` | Pobranie (auth) — ścieżka faktyczna w URLconf |
| POST | `/therapist/documents` | Upload przez terapeutę (`multipart`) |

---

## Terapeuta — profil i statystyki

| Metoda | Endpoint | Opis |
|--------|----------|------|
| GET | `/therapist/profile` | Biogram, kursy, PWZFz |
| PATCH | `/therapist/profile` | Edycja |
| GET | `/therapist/dashboard/stats` | Widgety pulpitu |
| GET | `/therapists/{id}/public` | Wizytówka dla pacjenta |

---

## Powiadomienia

| Metoda | Endpoint | Opis |
|--------|----------|------|
| GET | `/me/notification-preferences` | Preferencje |
| PATCH | `/me/notification-preferences` | Aktualizacja switchy |

---

## Pliki

Upload: `multipart/form-data`, max rozmiar konfigurowalny w `.env` (`MAX_UPLOAD_MB`).

Dozwolone MIME: `application/pdf`, `video/mp4`.

---

## Kolejne kroki

1. ~~Implementacja serializers + permissions w DRF~~ (Faza 2)
2. ~~Eksport kolekcji Postman~~ → [`postman/PhysioCare.json`](postman/PhysioCare.json), przewodnik [`postman-testing.md`](postman-testing.md)
3. Przejście checklisty Postman (wszystkie UC + wyjątki)
4. Walidacja kontraktu testami integracyjnymi (Faza 3)
