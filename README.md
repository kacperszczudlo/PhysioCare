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
| [docs/api.md](docs/api.md) | Kontrakt REST API (szkic) |
| [docs/diagrams/](docs/diagrams/) | ERD, architektura, moduły, use case (draw.io) |
| [database/schema.sql](database/schema.sql) | Schemat PostgreSQL |

## Diagramy

Otwórz pliki `.drawio` w [diagrams.net](https://app.diagrams.net) lub rozszerzeniu Draw.io w VS Code/Cursor:

- `docs/diagrams/erd.drawio` — model danych
- `docs/diagrams/architecture.drawio` — kontenery systemu
- `docs/diagrams/module-dependencies.drawio` — moduły Django
- `docs/diagrams/use-cases.drawio` — przypadki użycia

## Uruchomienie lokalne (po Fazie 1)

> Backend i frontendy zostaną dodane w kolejnych fazach. Poniżej docelowy sposób uruchomienia.

### Wymagania

- Python 3.12+
- Node.js 20 LTS
- PostgreSQL 16
- (Mobile) Expo CLI

### Konfiguracja

```bash
cp .env.example .env
# Uzupełnij wartości w .env
```

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

### Web

```bash
cd web
npm install
npm run dev
```

### Mobile

```bash
cd mobile
npm install
npx expo start
```

## Mockup UI

Referencja wizualna ekranów: plik `mockup_systemu_fizjoterapii.tsx` (poza repo — lokalny prototyp).

## Status projektu

**Faza 0** — dokumentacja i struktura monorepo (commit inicjalizacyjny).

## Licencja

Projekt inżynierski — ATAR, kierunek Informatyka, rok akademicki 2026/2027.
