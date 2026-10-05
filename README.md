# PhysioCare

Narzędzie do prowadzenia gabinetu fizjoterapeutycznego: panel WWW dla terapeuty, aplikacja mobilna dla pacjenta oraz jedno REST API.

## Opis

PhysioCare obsługuje:

- **panel terapeuty (web):** kalendarz wizyt, kartę pacjenta z epizodami, mapę ciała (VAS), katalog ćwiczeń, pliki dokumentacji oraz moduł opinii i ocen pacjentów;
- **aplikację pacjenta (mobile):** terminy wizyt, ćwiczenia domowe (compliance), wystawianie opinii i ocen specjalistom, dokumenty kliniczne (kierowanie, wyroby, Recepta na Ruch) oraz zgody RODO.

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
├── backend/          # Django + DRF (oraz backend/README.md)
├── web/              # Panel fizjoterapeuty (React + web/README.md)
├── mobile/           # Aplikacja pacjenta (Expo + mobile/README.md)
├── database/         # schema.sql - referencja schematu
├── docs/             # Dokumentacja, diagramy, API
├── .env.example      # Zmienne środowiskowe (szablon)
└── README.md
```

## Dokumentacja

| Dokument | Opis |
|----------|------|
| [docs/topic-selection.md](docs/topic-selection.md) | Temat, cel, zakres, technologie |
| [docs/architecture.md](docs/architecture.md) | Architektura systemu |
| [docs/use-cases.md](docs/use-cases.md) | Przypadki użycia |
| [docs/api.md](docs/api.md) | Kontrakt REST API |
| [docs/legal/polityka-prywatnosci.md](docs/legal/polityka-prywatnosci.md) | Polityka prywatności (RODO / PKE) |
| [docs/legal/polityka-cookies.md](docs/legal/polityka-cookies.md) | Polityka cookies i technologie w urządzeniu |
| [docs/monitoring.md](docs/monitoring.md) | Logi strukturalne, latency, request id |
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
Wszystkie komendy zakładają katalog główny repo (`PhysioCare/`) oraz środowisko **PowerShell** na Windowsie (wywołania npm zapisano jako `npm.cmd`).

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

W `.env` ustaw co najmniej: `POSTGRES_*`, `DJANGO_SECRET_KEY`, `DJANGO_ALLOWED_HOSTS` oraz
`FIELD_ENCRYPTION_KEY` (klucz Fernet przeznaczony wyłącznie do szyfrowania danych w bazie).
Opcjonalnie: `EMAIL_*` (reset hasła), `GOOGLE_CLIENT_IDS` (logowanie Google).

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

Do komfortowej pracy w VS Code otwórz **trzy terminale** (np. funkcja `Split Terminal`):

```
┌─────────────────────────┬─────────────────────────┬─────────────────────────┐
│  TERMINAL 1             │  TERMINAL 2             │  TERMINAL 3             │
│  Backend (Django API)   │  Web (Panel React)      │  Mobile (Metro / Expo)  │
└─────────────────────────┴─────────────────────────┴─────────────────────────┘
```

> **Wskazówka (Emulator Androida):** Przed startem aplikacji mobilnej uruchom wirtualny telefon (w VS Code: `Ctrl + Shift + P` → `Android iOS Emulator: Run Android Emulator` lub z poziomu *Virtual Device Manager* w Android Studio).

#### Terminal 1 — Backend (API)

REST: `http://127.0.0.1:8000/api/v1/` (lokalnie) oraz `http://<IP-LAN>:8000/api/v1/` (telefon w tej samej sieci Wi‑Fi).

Domyślny `runserver` bez hosta słucha tylko na `127.0.0.1` — telefon/emulator z `EXPO_PUBLIC_API_BASE_URL=http://<IP>:8000/...` wtedy **nie** połączy się z API. Dlatego startuj z `0.0.0.0:8000`:

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

Uruchomienie bezpośrednio na emulatorze Androida:

```powershell
cd mobile
npm.cmd run android
```

Lub start samego bundlera Metro w trybie **dev client** (`expo start --dev-client`):

```powershell
cd mobile
npm.cmd start
```

W terminalu Metro:

| Klawisz | Działanie |
|---------|-----------|
| `a` | otwórz na Androidzie (development build) |
| `w` | otwórz w przeglądarce |
| `s` | przełącz na Expo Go |
| `r` | przeładuj aplikację w emulatorze (Fast Refresh) |

Szybki UI bez native builda (tylko hasło, bez push / Google):

```powershell
npm.cmd run start:go
```

**Przydatne skróty emulatora:**
* **Menu deweloperskie Androida:** `Ctrl + M` w oknie emulatora.
* **Przeładowanie widoku:** podwójne naciśnięcie klawisza `R` w emulatorze.

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
# Pełna zjednoczona paczka (Backend Pytest + Web Vitest + Mobile Vitest):
python scripts/run_tests.py

# Weryfikacja kolekcji Postman:
python scripts/run_postman.py
```

Raporty: `backend/reports/pytest-report.html`, `backend/reports/coverage/index.html`.

**Postman** — import [docs/postman/PhysioCare.json](docs/postman/PhysioCare.json), `baseUrl=http://localhost:8000/api/v1`, Cookie Jar ON, URL-e ze slashami na końcu. Przewodnik: [docs/postman-testing.md](docs/postman-testing.md).

### Skrypty (`scripts/`)

| Skrypt | Opis |
|--------|------|
| `setup_postgres_auth.py` | User, baza, `btree_gist` |
| `reset_db.py` | Drop/create DB + migrate |
| `sync_schema_sql.py` | Dump schematu → `database/schema.sql` |
| `run_tests.py` | Pełna paczka testów (Backend + Web + Mobile) |
| `run_postman.py` | Weryfikacja i runner kolekcji Postman |

Uruchamianie zawsze z roota repo:

```powershell
python scripts/<nazwa>.py
```

Na Windowsie nie odpalaj skryptów dwuklikiem — użyj PowerShell / terminala Cursor.

## Skalowanie i Architektura Realtime (SSE)

Model domenowy łączy wielu terapeutów z wieloma pacjentami (wizyta = para terapeuta-pacjent). Warstwa czasu rzeczywistego (SSE) została przygotowana na skalowanie horyzontalne:

- **1 instancja / Demo / Dev**: Domyślna szyna `InMemorySseBus` w pamięci procesu (brak wymaganych dodatkowych usług).
- **Klastry / Wiele workerów (Produkcja)**: Szyna **Redis Pub/Sub** (`SSE_BUS_ENGINE="redis"` lub automatycznie po ustawieniu `REDIS_URL`). Zdarzenia emitowane przez dowolny worker trafiają do wszystkich otwartych strumieni SSE na innych instancjach.
- **Obserwowalność i Monitoring**: Metryki aktywnych strumieni SSE, unikalnych użytkowników i zdrowia Redisa dostępne pod `GET /api/v1/me/events/stats/`.

Kontrakt eventów (sygnał per `user_id` → klient robi refetch REST) pozostaje bez zmian.

## Licencja

Projekt inżynierski - ATAR, kierunek Informatyka, rok akademicki 2026/2027.
