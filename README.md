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

Poniżej pełna ścieżka od zera do działającego stacku: **API + panel web + aplikacja pacjenta**.  
Wszystkie komendy zakładają katalog główny repo (`PhysioCare/`) i **PowerShell** na Windowsie.  
Na Windowsie używaj zawsze `npm.cmd` (nie `npm`) — ExecutionPolicy blokuje `npm.ps1`.

### Wymagania

| Narzędzie | Wersja / uwagi |
|-----------|----------------|
| Python | 3.12+ |
| PostgreSQL | 16+ z rozszerzeniem `btree_gist` (Stack Builder → *PostgreSQL Database Server Contrib*) |
| Node.js | 20 LTS |
| PowerShell | 5.1+ |
| `psql` / `pg_dump` | w PATH albo w `C:\Program Files\PostgreSQL\<wersja>\bin` |
| (Mobile) | Expo Go **albo** Android Studio / urządzenie z development buildem — szczegóły w [mobile/README.md](mobile/README.md) |

### 1. Konfiguracja środowiska (raz)

Skopiuj szablon i uzupełnij sekrety oraz dane bazy:

```powershell
Copy-Item .env.example .env
```

W `.env` ustaw co najmniej: `POSTGRES_*`, `DJANGO_SECRET_KEY`, `DJANGO_ALLOWED_HOSTS`.  
Opcjonalnie: `EMAIL_*` (reset hasła), `GOOGLE_CLIENT_IDS` (logowanie Google) — patrz [docs/deployment.md](docs/deployment.md).

Jeśli PostgreSQL jest świeżo zainstalowany, utwórz użytkownika, bazę i `btree_gist`:

```powershell
# W .env: POSTGRES_ADMIN_USER=postgres + POSTGRES_ADMIN_PASSWORD=haslo-z-instalatora
python scripts/setup_postgres_auth.py
```

### 2. Pierwsze uruchomienie backendu

```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
cd physiocare
python manage.py migrate
```

Na tym etapie API jest gotowe do startu (`python manage.py runserver` — krok 4).

### 3. Zależności frontu (raz lub po zmianie `package.json`)

```powershell
cd web
npm.cmd install

cd ..\mobile
npm.cmd install
Copy-Item .env.example .env   # jeśli jeszcze nie ma mobile/.env
```

W `mobile/.env` ustaw `EXPO_PUBLIC_API_BASE_URL`:

| Gdzie działa appka | Wartość |
|--------------------|---------|
| Emulator Android | `http://10.0.2.2:8000/api/v1` |
| Telefon / fizyczne urządzenie (ta sama sieć Wi‑Fi co PC) | `http://<IP-LAN-PC>:8000/api/v1` |
| Expo web / iOS simulator | `http://localhost:8000/api/v1` |

Ten sam adres IP dodaj do `DJANGO_ALLOWED_HOSTS` w rootowym `.env` (np. `localhost,127.0.0.1,192.168.1.45`).

### 4. Codzienny start — trzy procesy

Stack wymaga **trzech osobnych terminali**. Kolejność ma znaczenie: najpierw API, potem klienci.

#### Terminal 1 — Backend (API)

REST: `http://127.0.0.1:8000/api/v1/` (lokalnie) oraz `http://<IP-LAN>:8000/api/v1/` (telefon w tej samej sieci Wi‑Fi).

Domyślny `runserver` bez hosta słucha tylko na `127.0.0.1` — telefon z `EXPO_PUBLIC_API_BASE_URL=http://<IP-LAN>:8000/...` wtedy **nie** połączy się z API. Dlatego startuj z `0.0.0.0:8000`:

```powershell
cd backend
.\venv\Scripts\Activate.ps1
cd physiocare
python manage.py runserver 0.0.0.0:8000
```

Live UI (SSE, `GET /api/v1/me/events/`) działa na `runserver`. Przy wielu równoległych streamach (demo/prod) preferuj ASGI — też na wszystkich interfejsach, jeśli testujesz mobile na telefonie:

```powershell
cd backend\physiocare
uvicorn physiocare.asgi:application --reload --host 0.0.0.0 --port 8000
```

Przypomnienia (wizyta 24h/2h, ćwiczenia na dziś) wymagają **osobnego** procesu — `runserver` / uvicorn ich nie odlicza:

```powershell
cd backend\physiocare
python manage.py run_notification_scheduler
```

#### Terminal 2 — Web (panel terapeuty)

Adres: `http://localhost:5173`. Vite proxy przekierowuje `/api` i `/media` na backend (`:8000`).

```powershell
cd web
npm.cmd run dev
```

Szczegóły (Google Sign-In, proxy SSE): [web/README.md](web/README.md).

#### Terminal 3 — Mobile (aplikacja pacjenta)

```powershell
cd mobile
npm.cmd start
```

Metro startuje w trybie **dev client** (`expo start --dev-client`). W terminalu Metro:

| Klawisz | Działanie |
|---------|-----------|
| `a` | otwórz na Androidzie (development build) |
| `w` | otwórz w przeglądarce |
| `s` | przełącz na Expo Go |
| `r` | przeładuj aplikację |

Szybki UI bez native builda (tylko hasło, bez push / Google):

```powershell
npm.cmd run start:go
```

Pełny opis (Expo Go vs native, push, Google): [mobile/README.md](mobile/README.md).

### 5. Narzędzia developerskie

**Reset bazy dev** (po konfliktach migracji):

```powershell
python scripts/reset_db.py
```

**Synchronizacja** `database/schema.sql` po `migrate`:

```powershell
python scripts/sync_schema_sql.py
```

**Lint / format**

```powershell
# Backend — Ruff (katalog `backend/`, venv aktywny)
pip install -r requirements.txt
ruff check physiocare tests
ruff format --check physiocare tests

# Web
cd web
npm.cmd run lint
npm.cmd run format:check

# Mobile
cd mobile
npm.cmd run lint
npm.cmd run format:check
```

**Testy** (z roota repo, PostgreSQL działa, venv w `backend/venv`):

```powershell
python scripts/run_tests.py
```

Raporty: `backend/reports/pytest-report.html`, `backend/reports/coverage/index.html`.

**Postman** — import [docs/postman/PhysioCare.json](docs/postman/PhysioCare.json), `baseUrl=http://localhost:8000/api/v1`, Cookie Jar ON, URL-e ze slashami na końcu. Przewodnik: [docs/postman-testing.md](docs/postman-testing.md).

### Skrypty (`scripts/`)

| Skrypt | Opis |
|--------|------|
| `setup_postgres_auth.py` | User, baza, `btree_gist` |
| `reset_db.py` | Drop/create DB + migrate |
| `sync_schema_sql.py` | Dump schematu → `database/schema.sql` |
| `run_tests.py` | pytest + coverage HTML |

Uruchamianie zawsze z roota repo:

```powershell
python scripts/<nazwa>.py
```

Na Windowsie nie odpalaj skryptów dwuklikiem — użyj PowerShell / terminala Cursor.

## Mockup UI

Referencja wizualna ekranów: plik `mockup_systemu_fizjoterapii.tsx` (poza repo - lokalny prototyp).

## Status projektu

**Faza 0-3** - dokumentacja, modele, REST API, Postman, testy backendu.  
**Faza 4 (branch `feat/web`)** - panel webowy terapeuty: auth, pulpit, harmonogram, pacjenci, ćwiczenia, profil (4.1-4.7).  
**Faza 5 (branch `feat/mobile`)** - aplikacja mobilna pacjenta (Expo): auth RODO, pulpit, wizyty, profil, stack szczegółów (5.1-5.7).  
**Faza 6 (branch `feat/refactor`)** - Ruff / ESLint / Prettier, monitoring (logi JSON + latency), checklist E2E, przewodnik wdrożenia, konspekt prezentacji.  
**Live UI (SSE)** - `GET /api/v1/me/events/`: Harmonogram/Pulpit web + Pulpit/Wizyty/Dokumenty/ćwiczenia mobile; demo: uvicorn ASGI (patrz [docs/deployment.md](docs/deployment.md), [docs/e2e-checklist.md](docs/e2e-checklist.md#live-ui-sse)).

## Skalowanie i Architektura Realtime (SSE)

Model domenowy łączy wielu terapeutów z wieloma pacjentami (wizyta = para terapeuta-pacjent). Warstwa czasu rzeczywistego (SSE) została przygotowana na skalowanie horyzontalne:

- **1 instancja / Demo / Dev**: Domyślna szyna `InMemorySseBus` w pamięci procesu (brak wymaganych dodatkowych usług).
- **Klastry / Wiele workerów (Produkcja)**: Szyna **Redis Pub/Sub** (`SSE_BUS_ENGINE="redis"` lub automatycznie po ustawieniu `REDIS_URL`). Zdarzenia emitowane przez dowolny worker trafiają do wszystkich otwartych strumieni SSE na innych instancjach.

Kontrakt eventów (sygnał per `user_id` → klient robi refetch REST) pozostaje bez zmian.

## Licencja

Projekt inżynierski - ATAR, kierunek Informatyka, rok akademicki 2026/2027.
