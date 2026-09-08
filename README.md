# PhysioCare

Narzędzie do prowadzenia gabinetu fizjoterapeutycznego: panel WWW dla terapeuty, aplikacja mobilna dla pacjenta oraz jedno REST API.

## Opis

PhysioCare obsługuje:

- **panel terapeuty (web):** kalendarz wizyt, kartę pacjenta z epizodami, mapę ciała (VAS), katalog ćwiczeń i pliki dokumentacji;
- **aplikację pacjenta (mobile):** terminy, ćwiczenia domowe (compliance), dokumenty kliniczne (kierowanie, wyroby, Recepta na Ruch) oraz zgody RODO.

## Stos technologiczny

| Warstwa | Technologia |
|---------|-------------|
| Backend | Python 3.12+, Django 6, Django REST Framework |
| Baza danych | PostgreSQL 16 |
| Web | React 19, Vite, TypeScript |
| Mobile | React Native (Expo), TypeScript |
| Auth | JWT (access + refresh) |

Zgodnie z zatwierdzonym tematem pracy - szczegóły są w [docs/topic-selection.md](docs/topic-selection.md).

## Struktura repozytorium

```
PhysioCare/
├── backend/          # Django + DRF
├── web/              # Panel fizjoterapeuty (React)
├── mobile/           # Aplikacja pacjenta (Expo)
├── database/         # schema.sql - referencja schematu
├── docs/             # Dokumentacja, diagramy, API
├── .env.example      # Zmienne środowiskowe (szablon)
└── README.md
```

## Dokumentacja

| Dokument | Opis |
|----------|------|
| [docs/topic-selection.md](docs/topic-selection.md) | Temat, cel, zakres, technologie |
| [docs/development-plan.md](docs/development-plan.md) | Plan realizacji krok po kroku |
| [docs/architecture.md](docs/architecture.md) | Architektura systemu |
| [docs/use-cases.md](docs/use-cases.md) | Przypadki użycia |
| [docs/api.md](docs/api.md) | Kontrakt REST API |
| [docs/legal/polityka-prywatnosci.md](docs/legal/polityka-prywatnosci.md) | Polityka prywatności (RODO / PKE) |
| [docs/legal/polityka-cookies.md](docs/legal/polityka-cookies.md) | Polityka cookies i technologie w urządzeniu |
| [docs/monitoring.md](docs/monitoring.md) | Logi strukturalne, latency, request id |
| [docs/e2e-checklist.md](docs/e2e-checklist.md) | Checklist ścieżek krytycznych |
| [docs/deployment.md](docs/deployment.md) | Wdrożenie demo (Railway / VPS / EAS) |
| [docs/presentation-outline.md](docs/presentation-outline.md) | Konspekt prezentacji |
| [docs/postman-testing.md](docs/postman-testing.md) | Kolekcja Postman, macierz UC, checklista |
| [docs/postman/PhysioCare.json](docs/postman/PhysioCare.json) | Importowalna kolekcja Postman |
| [docs/diagrams/](docs/diagrams/) | ERD, architektura, moduły, use case (draw.io) |
| [database/schema.sql](database/schema.sql) | Schemat PostgreSQL |

## Diagramy

Otwórz pliki `.drawio` w [diagrams.net](https://app.diagrams.net) lub rozszerzeniu Draw.io w VS Code/Cursor:

- `docs/diagrams/erd.drawio` - model danych
- `docs/diagrams/architecture.drawio` - kontenery systemu
- `docs/diagrams/module-dependencies.drawio` - moduły Django
- `docs/diagrams/use-cases.drawio` - przypadki użycia

## Uruchomienie lokalne

### Wymagania

- Python 3.12+
- PostgreSQL 16+ (+ rozszerzenie `btree_gist` / Stack Builder -> *PostgreSQL Database Server Contrib*)
- Node.js 20 LTS (web/mobile - Faza 4+)
- (Mobile) Expo CLI
- (Windows) PowerShell 5.1+; binaria `psql` / `pg_dump` w PATH lub w `C:\Program Files\PostgreSQL\<wersja>\bin`

### Konfiguracja

```powershell
Copy-Item .env.example .env
# Uzupelnij wartosci w .env (POSTGRES_*, DJANGO_SECRET_KEY)
# Opcjonalnie EMAIL_* (Mailtrap) - reset hasła przez link; patrz docs/deployment.md
```

**Pierwsza konfiguracja PostgreSQL:**

```powershell
# W .env: POSTGRES_ADMIN_USER=postgres + POSTGRES_ADMIN_PASSWORD=haslo-z-instalatora
python scripts/setup_postgres_auth.py
```

### Backend

```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
cd physiocare
python manage.py migrate
python manage.py runserver
```

Live UI (SSE, `GET /api/v1/me/events/`) działa też na `runserver`. Przy wielu równoległych streamach (demo/prod) preferuj ASGI:

```powershell
cd backend\physiocare
uvicorn physiocare.asgi:application --reload --host 127.0.0.1 --port 8000
```

Przypomnienia (wizyta 24h/2h, ćwiczenia na dziś) wymagają **drugiego** procesu - `runserver` / uvicorn ich sam nie odlicza:

```powershell
cd backend\physiocare
python manage.py run_notification_scheduler
```

**Reset bazy dev (po zmianie migracji):**

```powershell
python scripts/reset_db.py
```

**Synchronizacja `database/schema.sql` po migrate:**

```powershell
python scripts/sync_schema_sql.py
```

### Jakość kodu (lint / format)

```powershell
# Backend - Ruff (z katalogu `backend/`, venv aktywny)
pip install -r requirements.txt
ruff check physiocare tests
ruff format --check physiocare tests

# Web - ESLint + Prettier (+ Oxlint)
cd web
npm install
npm run lint
npm run format:check

# Mobile - ESLint + Prettier + tsc
cd mobile
npm install
npm run lint
npm run format:check
```

### Testy

Wszystkie komendy z katalogu głównego repo (`PhysioCare/`), przy działającym PostgreSQL i venv w `backend/venv`.

**1) Testy jednostkowe / integracyjne (pytest + coverage)**

```powershell
python scripts/run_tests.py
```

Raporty:
- `backend/reports/pytest-report.html`
- `backend/reports/coverage/index.html`

**2) Kolekcja Postman** - import `docs/postman/PhysioCare.json`, `baseUrl=http://localhost:8000/api/v1`, Cookie Jar ON. URL-e ze slashami na końcu.

### Web

```powershell
cd web
npm install
npm run dev
```

### Mobile

```powershell
cd mobile
npm install
npx expo start
```

### Skrypty (`scripts/`) - Python

| Skrypt | Opis |
|--------|------|
| `setup_postgres_auth.py` | User, baza, `btree_gist` |
| `reset_db.py` | Drop/create DB + migrate |
| `sync_schema_sql.py` | Dump schematu -> `database/schema.sql` |
| `run_tests.py` | pytest + coverage HTML |

Uruchamianie (zawsze z roota repo):

```powershell
python scripts/<nazwa>.py
```

Na Windows nie odpalaj dwuklikiem - użyj PowerShell / terminala Cursor.
## Mockup UI

Referencja wizualna ekranów: plik `mockup_systemu_fizjoterapii.tsx` (poza repo - lokalny prototyp).

## Status projektu

**Faza 0-3** - dokumentacja, modele, REST API, Postman, testy backendu.  
**Faza 4 (branch `feat/web`)** - panel webowy terapeuty: auth, pulpit, harmonogram, pacjenci, ćwiczenia, profil (4.1-4.7).  
**Faza 5 (branch `feat/mobile`)** - aplikacja mobilna pacjenta (Expo): auth RODO, pulpit, wizyty, profil, stack szczegółów (5.1-5.7).  
**Faza 6 (branch `feat/refactor`)** - Ruff / ESLint / Prettier, monitoring (logi JSON + latency), checklist E2E, przewodnik wdrożenia, konspekt prezentacji.  
**Live UI (SSE)** - `GET /api/v1/me/events/`: Harmonogram/Pulpit web + Pulpit/Wizyty/Dokumenty/ćwiczenia mobile; demo: uvicorn ASGI (patrz [docs/deployment.md](docs/deployment.md), [docs/e2e-checklist.md](docs/e2e-checklist.md#live-ui-sse)).

## Na później (skalowanie)

Model domenowy już łączy wielu terapeutów z wieloma pacjentami (wizyta = para terapeuta-pacjent). Przy większym ruchu i live UI (SSE: harmonogram / wizyty / dokumenty / ćwiczenia) bolą nie relacje N×M, tylko **infrastruktura połączeń**:

| Ból | Dlaczego | Kierunek rozwiązania |
|-----|----------|----------------------|
| Wiele otwartych SSE naraz | Sync Gunicorn trzyma workera na czas streamu → reszta API zwalnia | Uruchamiać API na **ASGI (uvicorn/daphne)**, nie na samym WSGI pod długie streamy |
| Kilka workerów / instancji | Event wyemitowany w jednym procesie nie dociera do streamu w innym | **Redis pub/sub** (lub równoważny bus) zamiast kolejki tylko w pamięci procesu |
| Demo vs produkcja | Mało równoległych sesji = in-memory wystarczy | Na demo: ASGI + 1 instancja; przy wzroście użytkowników: Redis + monitoring liczby streamów |

Kontrakt eventów (sygnał per `user_id` → klient robi refetch REST) zostaje - nie trzeba przebudowywać feature’u pod klinikę z wieloma fizjo i pacjentami, tylko podnieść warstwę realtime.

## Licencja

Projekt inżynierski - ATAR, kierunek Informatyka, rok akademicki 2026/2027.
