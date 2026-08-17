# Architektura systemu PhysioCare

## Przegląd

PhysioCare składa się z trzech części: panelu React, klienta Expo i jednego backendu REST nad PostgreSQL. Oba fronty mówią z API wyłącznie przez HTTPS i JSON.

```
+-----------------+     +-----------------+
|  Web (React)    |     | Mobile (Expo)   |
|  Fizjoterapeuta |     | Pacjent         |
+--------+--------+     +--------+--------+
         |    HTTPS / JSON       |
         +----------+------------+
                    v
         +----------------------+
         |  Django REST API     |
         |  JWT + Role Guard    |
         +----------+-----------+
                    |
         +----------+-----------+
         v                      v
   +-----------+         +-------------+
   | PostgreSQL|         | File Storage|
   |           |         | PDF / mp4   |
   +-----------+         +-------------+
```

Szczegółowy rysunek kontenerów: [diagrams/architecture.drawio](diagrams/architecture.drawio).

## Aktorzy i role

| Aktor | Klient | Rola API |
|-------|--------|----------|
| Fizjoterapeuta | Web | `THERAPIST` |
| Pacjent | Mobile | `PATIENT` |

Reguły dostępu obowiązują **tylko na serwerze**. Klient może ukryć przyciski, ale nie jest źródłem prawdy.

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

Osobna teczka konkretnego problemu (np. skręcenie kostki w 2024 i ból kręgosłupa w 2026). W środku:

- status (`IN_PROGRESS`, `COMPLETED_SUCCESS`, `REFERRED`, `INTERRUPTED`),
- kod ICD-10 (opcjonalnie),
- wpisy mapy ciała (BodyAreaPain),
- notatki z wizyt,
- powiązane przypisania ćwiczeń.

### Wizyta (Visit)

Slot w kalendarzu terapeuty. Statusy: `SCHEDULED`, `COMPLETED`, `CANCELLED`, `NO_SHOW`. Wizyta wskazuje epizod i typ terapii (kolor w siatce).

### Compliance ćwiczeń

`ExerciseAssignment` ustala dawkę i przedział dat. Pacjent zaznacza wykonanie dnia — `ExerciseCompletion` (unikalność: assignment + data).

### Zgody RODO

- **Wymagane** (regulamin, dane medyczne): data zawarcia, brak cofnięcia bez usunięcia konta.
- **Opcjonalne** (marketing, badania): przełączane w profilu.
- **Dokumenty prawne:** [Polityka prywatności](legal/polityka-prywatnosci.md), [Polityka cookies](legal/polityka-cookies.md); w UI: web `/privacy`, `/cookies`, `/account-deletion`; mobile `/legal/*`.

## Przepływy krytyczne

### 1. Przypisanie ćwiczenia (web -> mobile)

```
Terapeuta: Baza ćwiczeń -> Przypisz -> wybór pacjenta, dawkowanie, okres
    -> POST /api/exercise-assignments/
Pacjent: Pulpit -> „Zalecenia na dziś” -> GET /api/me/exercises/today
    -> POST /api/exercise-completions/ (oznaczenie wykonania)
```

### 2. Mapa ciała (Diagnostic Mapper)

```
Terapeuta: Karta pacjenta -> klik regionu anatomicznego -> VAS + charakter bólu
    -> opcjonalnie cele leczenia (staw / mięsień / kość / tkanka)
    -> POST /api/episodes/{id}/body-pain/
Epizod: lista plakietek pod „Bieżąca diagnoza”
```

### 3. Zmiana / odwołanie wizyty (mobile)

```
Pacjent: Szczegóły wizyty -> Modal zmiany terminu / odwołania
    -> PATCH /api/visits/{id}/  lub  POST /api/visits/{id}/cancel/
Terapeuta: widok w harmonogramie i karcie pacjenta (ten sam zasób Visit)
```

## Bezpieczeństwo (skrót)

- Hasła: hashery Django na `AbstractBaseUser` (domyślnie PBKDF2/argon w zależności od wersji; walidatory siły hasła)
- JWT: krótki access; refresh w httpOnly cookie (web) albo SecureStore (mobile); wylogowanie i zmiana hasła wpisują refresh na czarną listę
- CORS: lista dozwolonych originów web + Expo
- Limit ciała żądania: Django `DATA_UPLOAD_MAX_MEMORY_SIZE`
- Pliki medyczne: JWT + własność rekordu; typ pliku z sygnatury bajtów, nie z nagłówka klienta
- Throttle na `/api/v1/auth/login/`

## Stack technologiczny

Zgodnie z tematem zatwierdzonym przez prowadzącego — [topic-selection.md](topic-selection.md).

## Powiązane dokumenty

- [use-cases.md](use-cases.md) - przypadki użycia
- [api.md](api.md) - kontrakt REST
- [diagrams/erd.drawio](diagrams/erd.drawio) - model danych
- [development-plan.md](development-plan.md) - harmonogram prac
