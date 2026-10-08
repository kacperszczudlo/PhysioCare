# PhysioCare Backend - REST API & Realtime Service

Warstwa serwerowa systemu PhysioCare dostarczająca jednolite API REST (`/api/v1`) oraz obsługę zdarzeń czasu rzeczywistego (Server-Sent Events) dla panelu fizjoterapeuty (Web) i aplikacji pacjenta (Mobile).

Zbudowana w oparciu o **Python 3.12+**, **Django 6** oraz **Django REST Framework**.

---

## Stos technologiczny

| Komponent | Technologia |
| :--- | :--- |
| Język / Framework | Python 3.12+, Django 6, Django REST Framework |
| Baza danych | PostgreSQL 16 (z rozszerzeniem `btree_gist` dla wykluczeń czasowych) |
| Autoryzacja | JWT (HttpOnly Cookie dla Web, Bearer Header dla Mobile) |
| Realtime / SSE | Server-Sent Events (`InMemorySseBus` dla dev / `Redis PubSub` dla prod) |
| Testowanie & Jakość | Pytest, Pytest-Django, Ruff (Linter & Formatter) |

---

## Moduły aplikacji Django (`physiocare/`)

- `accounts` – Obsługa użytkowników, autoryzacja JWT, rejestracja, reset hasła, role (PATIENT, THERAPIST, ADMIN) oraz logowanie Google.
- `administration` – Moduł panelu administratora: analityka KPI, zarządzanie użytkownikami, zbiorczy grafik, audyt personelu, moderacja opinii.
- `therapists` – Profile fizjoterapeutów, weryfikacja numerów PWZFz, ustawienia gabinetów.
- `patients` – Kartoteka pacjentów, historie epizodów chorobowych, mapa bólów (VAS).
- `scheduling` – Harmonogram wizyt, wykrywanie nakładania terminów (PostgreSQL GIST constraints).
- `exercises` – Katalog ćwiczeń fizjoterapeutycznych i przydzielanie planów treningowych pacjentom.
- `documents` – Pliki dokumentacji medycznej (zaświadczenia, skierowania, "Recepta na Ruch").
- `reviews` – System opinii i ocen pacjentów z automatycznym odświeżaniem wskaźników jakości gabinetu.
- `privacy` – Moduł zgód RODO oraz rejestracji przetwarzania danych.
- `notifications` – Harmonogram i wysyłka przypomnień e-mail oraz powiadomień Push (Expo/FCM).
- `core` – Klasy bazowe, wyjątki, middleware, uprawnienia (RBAC / IsAdminRole) oraz mechanizmy szyny zdarzeń SSE.

---

## Uruchomienie i Skrypty

### 1. Przygotowanie środowiska

```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
cd physiocare
python manage.py migrate
```

### 2. Uruchomienie serwera deweloperskiego API

```powershell
# Domyślny serwer HTTP (słuchający na wszystkich interfejsach pod aplikację mobilną):
python manage.py runserver 0.0.0.0:8000
```

### 3. Usługa przypomnień (Scheduler)

W osobnym terminalu należy uruchomić proces odliczania powiadomień i przypomnień:

```powershell
python manage.py run_notification_scheduler
```

### 4. Tworzenie konta Administratora (Role Isolation)

Zgodnie z regułami bezpieczeństwa konta administratora nie można utworzyć przez publiczne formularze rejestracji. Użyj skryptu pomocniczego z katalogu głównego projektu:

```powershell
python ..\scripts\create_admin.py --email admin@physiocare.pl --password "TwojeHaslo123!"
```

Lub z poziomu Django CLI:

```powershell
python manage.py createsuperuser
```

### 5. Testy i Jakość Kodu

```powershell
# Testy jednostkowe i integracyjne (pytest)
pytest

# Weryfikacja jakości kodu (Ruff)
ruff check physiocare tests
ruff format --check physiocare tests
```
