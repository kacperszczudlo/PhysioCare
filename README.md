# PhysioCare

System wspomagania zarządzania gabinetem fizjoterapeutycznym — aplikacja webowa (fizjoterapeuta), mobilna (pacjent) i wspólny backend REST API.

## Opis

PhysioCare umożliwia:

- **Fizjoterapeucie (web):** harmonogram wizyt, karta pacjenta z epizodami leczenia, mapa ciała (VAS), baza ćwiczeń, dokumentacja.
- **Pacjentowi (mobile):** przegląd wizyt, realizacja ćwiczeń domowych (compliance), dokumenty PDF, zgody RODO.

## Stos technologiczny

| Warstwa | Technologia |
|---------|-------------|
| Backend | Python 3.12+, Django 5, Django REST Framework |
| Baza danych | PostgreSQL 16 |
| Web | React 19, Vite, TypeScript |
| Mobile | React Native (Expo), TypeScript |
| Auth | JWT (access + refresh) |

Zgodnie z zatwierdzonym tematem pracy — szczegóły w [docs/topic-selection.md](docs/topic-selection.md).

## Struktura repozytorium

```
PhysioCare/
├── backend/          # Django + DRF (do inicjalizacji w Fazie 1)
├── web/              # Panel fizjoterapeuty (React)
├── mobile/           # Aplikacja pacjenta (Expo)
├── database/         # schema.sql — referencja schematu
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
| [docs/postman-testing.md](docs/postman-testing.md) | Kolekcja Postman, macierz UC, checklista |
| [docs/postman/PhysioCare.json](docs/postman/PhysioCare.json) | Importowalna kolekcja Postman |
| [docs/diagrams/](docs/diagrams/) | ERD, architektura, moduły, use case (draw.io) |
| [database/schema.sql](database/schema.sql) | Schemat PostgreSQL |

## Diagramy

Otwórz pliki `.drawio` w [diagrams.net](https://app.diagrams.net) lub rozszerzeniu Draw.io w VS Code/Cursor:

- `docs/diagrams/erd.drawio` — model danych
- `docs/diagrams/architecture.drawio` — kontenery systemu
- `docs/diagrams/module-dependencies.drawio` — moduły Django
- `docs/diagrams/use-cases.drawio` — przypadki użycia

## Uruchomienie lokalne

### Wymagania

- Python 3.12+
- PostgreSQL 16+ (+ rozszerzenie `btree_gist` / Stack Builder → *PostgreSQL Database Server Contrib*)
- Node.js 20 LTS (web/mobile — Faza 4+)
- (Mobile) Expo CLI
- (Windows) PowerShell 5.1+; binaria `psql` / `pg_dump` w PATH lub w `C:\Program Files\PostgreSQL\<wersja>\bin`

### Konfiguracja

```powershell
Copy-Item .env.example .env
# Uzupelnij wartosci w .env (POSTGRES_*, DJANGO_SECRET_KEY)
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

**Reset bazy dev (po zmianie migracji):**

```powershell
python scripts/reset_db.py
```

**Synchronizacja `database/schema.sql` po migrate:**

```powershell
python scripts/sync_schema_sql.py
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

**2) Smoke use-case API (wymaga `runserver` na :8000)**

```powershell
# terminal 1
cd backend\physiocare
..\venv\Scripts\python.exe manage.py runserver

# terminal 2 — z root repo
.\backend\venv\Scripts\python.exe scripts\run_api_usecases.py
```

**3) Kolekcja Postman** — import `docs/postman/PhysioCare.json`, `baseUrl=http://localhost:8000/api/v1`, Cookie Jar ON. URL-e ze slashami na końcu.

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

### Skrypty (`scripts/`) — Python

| Skrypt | Opis |
|--------|------|
| `setup_postgres_auth.py` | User, baza, `btree_gist` |
| `reset_db.py` | Drop/create DB + migrate |
| `sync_schema_sql.py` | Dump schematu → `database/schema.sql` |
| `run_tests.py` | pytest + coverage HTML |
| `run_api_usecases.py` | Smoke UC-01–18 przeciwko lokalnemu API |
| `grant_test_db_privileges.py` | Opcjonalnie `CREATEDB` |
| `generate_postman_collection.py` | Regeneracja kolekcji Postman |

Uruchamianie (zawsze z roota repo):

```powershell
python scripts/<nazwa>.py
```

Na Windows nie odpalaj dwuklikiem — użyj PowerShell / terminala Cursor.
## Mockup UI

Referencja wizualna ekranów: plik `mockup_systemu_fizjoterapii.tsx` (poza repo — lokalny prototyp).

## Status projektu

**Faza 0–3** — dokumentacja, modele, REST API, Postman, testy backendu.  
**Faza 4 (branch `feat/web`)** — panel webowy terapeuty: auth, pulpit, harmonogram, pacjenci, ćwiczenia, profil (4.1–4.7).  
**Faza 5 (branch `feat/mobile`)** — aplikacja mobilna pacjenta (Expo): auth RODO, pulpit, wizyty, profil, stack szczegółów (5.1–5.7).  
**Następna:** Faza 6 — jakość, monitoring, finalizacja.

## Licencja

Projekt inżynierski — ATAR, kierunek Informatyka, rok akademicki 2026/2027.
