# Architektura systemu PhysioCare

## Przegląd

PhysioCare to system trójwarstwowy: dwa klienty (web, mobile) komunikują się z jednym backendem REST nad PostgreSQL.

```
┌─────────────────┐     ┌─────────────────┐
│  Web (React)    │     │ Mobile (Expo)   │
│  Fizjoterapeuta │     │ Pacjent         │
└────────┬────────┘     └────────┬────────┘
         │    HTTPS / JSON       │
         └──────────┬────────────┘
                    ▼
         ┌──────────────────────┐
         │  Django REST API     │
         │  JWT + Role Guard    │
         └──────────┬───────────┘
                    │
         ┌──────────┴───────────┐
         ▼                      ▼
   ┌───────────┐         ┌─────────────┐
   │ PostgreSQL│         │ File Storage│
   │           │         │ PDF / mp4   │
   └───────────┘         └─────────────┘
```

Diagram szczegółowy: [diagrams/architecture.drawio](diagrams/architecture.drawio)

## Aktorzy i role

| Aktor | Klient | Rola API |
|-------|--------|----------|
| Fizjoterapeuta | Web | `THERAPIST` |
| Pacjent | Mobile | `PATIENT` |

Reguły autoryzacji są egzekwowane **wyłącznie na serwerze**. Klient ukrywa niedostępne UI, ale nie stanowi źródła prawdy.

## Moduły backendu (Django apps)

| App | Odpowiedzialność |
|-----|------------------|
| `core` | Ustawienia, URL, middleware, error handler |
| `accounts` | User, JWT, rejestracja, reset hasła |
| `patients` | PatientProfile, dane kontaktowe |
| `therapists` | TherapistProfile, PWZFz, biogram, kursy |
| `treatment` | TreatmentEpisode, BodyAreaPain, VisitNote |
| `scheduling` | Visit, TherapyType, dostępność |
| `exercises` | Exercise, kategorie, przypisania, compliance |
| `documents` | MedicalDocument, upload/download |
| `privacy` | Consent, eksport danych, wniosek o usunięcie |
| `notifications` | NotificationPreference (kanały w MVP: stub) |

Zależności modułów: [diagrams/module-dependencies.drawio](diagrams/module-dependencies.drawio)

## Kluczowe koncepcje domenowe

### Epizod leczenia (Treatment Episode)

Osobna „teczka” problemu medycznego dla pacjenta (np. skręcona kostka 2024 vs. ból kręgosłupa 2026). Zawiera:

- status (`IN_PROGRESS`, `COMPLETED_SUCCESS`, `REFERRED`, `INTERRUPTED`),
- kod ICD-10 (opcjonalnie),
- wpisy mapy ciała (BodyAreaPain),
- notatki z wizyt,
- powiązane przypisania ćwiczeń.

### Wizyta (Visit)

Termin w harmonogramie terapeuty. Statusy: `SCHEDULED`, `COMPLETED`, `CANCELLED`, `NO_SHOW`. Powiązana z epizodem i typem terapii (kolor w kalendarzu).

### Compliance ćwiczeń

`ExerciseAssignment` definiuje dawkowanie i okres. Pacjent oznacza wykonanie dziennie → `ExerciseCompletion` (unikalność: assignment + data).

### Zgody RODO

- **Wymagane** (regulamin, dane medyczne): data zawarcia, brak cofnięcia bez usunięcia konta.
- **Opcjonalne** (marketing, badania): przełączane w profilu.

## Przepływy krytyczne

### 1. Przypisanie ćwiczenia (web → mobile)

```
Terapeuta: Baza ćwiczeń → Przypisz → wybór pacjenta, dawkowanie, okres
    → POST /api/exercise-assignments/
Pacjent: Pulpit → „Zalecenia na dziś” → GET /api/me/exercises/today
    → POST /api/exercise-completions/ (oznaczenie wykonania)
```

### 2. Mapa ciała (Diagnostic Mapper)

```
Terapeuta: Karta pacjenta → klik regionu anatomicznego → VAS + charakter bólu
    → opcjonalnie cele leczenia (staw / mięsień / kość / tkanka)
    → POST /api/episodes/{id}/body-pain/
Epizod: lista plakietek pod „Bieżąca diagnoza”
```

### 3. Zmiana / odwołanie wizyty (mobile)

```
Pacjent: Szczegóły wizyty → Modal zmiany terminu / odwołania
    → PATCH /api/visits/{id}/  lub  POST /api/visits/{id}/cancel/
Terapeuta: widok w harmonogramie i karcie pacjenta (ten sam zasób Visit)
```

## Bezpieczeństwo (skrót)

- Hasła: bcrypt (Django `AbstractUser` + walidatory)
- JWT: krótki access, refresh w httpOnly cookie lub secure storage (mobile)
- CORS: whitelist domen web + Expo dev
- `express.json` limit → analog w Django: `DATA_UPLOAD_MAX_MEMORY_SIZE`
- Pliki medyczne: autoryzacja per pacjent/terapeuta, signed URLs opcjonalnie
- Rate limiting na `/api/auth/login`

## Stack technologiczny

Zgodnie z tematem zatwierdzonym przez prowadzącego — patrz [topic-selection.md](topic-selection.md).

## Powiązane dokumenty

- [use-cases.md](use-cases.md) — przypadki użycia
- [api.md](api.md) — kontrakt REST
- [diagrams/erd.drawio](diagrams/erd.drawio) — model danych
- [development-plan.md](development-plan.md) — harmonogram prac
