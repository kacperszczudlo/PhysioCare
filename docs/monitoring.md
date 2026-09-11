# Monitoring i logowanie - PhysioCare

Opis warstwy obserwowalności (Faza 6.2-6.3): strukturalne logi serwera oraz metryki czasu odpowiedzi HTTP.

## Cele

- Szybka diagnoza błędów API bez czytania stacktrace w przeglądarce
- Korelacja żądań przez `X-Request-ID`
- Podstawowa metryka latency na każde żądanie (`X-Response-Time-Ms` + log)

## Konfiguracja

| Zmienna | Domyślnie | Opis |
|---------|-----------|------|
| `LOG_FORMAT` | `text` gdy `DJANGO_DEBUG=true`, inaczej `json` | Format logów konsoli |
| `DJANGO_DEBUG` | - | Wpływa na domyślny format i ujawnianie 500 w odpowiedzi |

Przykład w `.env`:

```env
LOG_FORMAT=json
```

## Strukturalne logi (JSON)

Logger `physiocare.api` emituje linie JSON (formatter `StructuredJsonFormatter`):

```json
{
  "timestamp": "2026-08-05T15:30:00.123456+00:00",
  "level": "INFO",
  "logger": "physiocare.api",
  "message": "request completed",
  "request_id": "a1b2c3d4-…",
  "method": "GET",
  "path": "/api/v1/patients/",
  "status_code": 200,
  "duration_ms": 12.4,
  "user_id": 7
}
```

Dodatkowe pola przy błędach DRF / nieobsłużonych wyjątkach:

| Pole | Znaczenie |
|------|-----------|
| `error_code` | Kod z envelope API (`VALIDATION_ERROR`, `SERVER_ERROR`, …) |
| `view` | Nazwa klasy widoku |
| `exception` | Stacktrace (tylko przy `logger.exception`) |

Logger `physiocare.auth` - zdarzenia auth (m.in. nieudane logowanie).

Logger `django.request` - ostrzeżenia/błędy frameworka Django.

## Middleware czasu odpowiedzi

`core.middleware.RequestTimingMiddleware` (na końcu łańcucha middleware):

1. Odczytuje lub generuje `X-Request-ID`
2. Mierzy czas obsługi (`perf_counter`)
3. Ustawia nagłówki odpowiedzi:
   - `X-Request-ID`
   - `X-Response-Time-Ms` (ms, jedno miejsce po przecinku)
4. Loguje `request completed` na poziomie INFO / WARNING (≥400) / ERROR (≥500)

Pomijane ścieżki: `/static/`, `/media/`, `/favicon.ico`.

## Envelope błędów API

Niezmieniony kontrakt z `docs/api.md`:

```json
{
  "error": {
    "code": "…",
    "message": "…",
    "details": {}
  }
}
```

Każdy błąd DRF jest dodatkowo logowany (WARNING/ERROR) z `request_id` i `error_code`. Nieobsłużone wyjątki w produkcji zwracają generyczny `SERVER_ERROR` i pełny stacktrace tylko w logach.

## Jak czytać logi lokalnie

```powershell
cd backend\physiocare
..\venv\Scripts\python.exe manage.py runserver
# w drugim terminalu - przykładowe żądanie
curl -i http://127.0.0.1:8000/api/v1/
```

Sprawdź w odpowiedzi nagłówki `X-Request-ID` i `X-Response-Time-Ms`, a w konsoli serwera odpowiadający wpis logu.

## Produkcja / hosting

- Ustaw `DJANGO_DEBUG=false` i `LOG_FORMAT=json`
- Przekieruj stdout kontenera / procesu do agregatora (Railway logs, journald, Loki, CloudWatch)
- Filtruj po `request_id` przy zgłoszeniu błędu od użytkownika (klient może odesłać wartość z nagłówka)

## Alerting (Sentry)

Ustaw `SENTRY_DSN` w środowisku produkcyjnym / staging. SDK inicjuje się w `settings.py` tylko gdy DSN jest niepusty:

| Zmienna | Opis |
|---------|------|
| `SENTRY_DSN` | DSN projektu Sentry |
| `SENTRY_ENVIRONMENT` | np. `staging` / `production` |
| `SENTRY_TRACES_SAMPLE_RATE` | domyślnie `0.1` |

Bez DSN błędy nadal trafiają do strukturalnych logów (`physiocare.api` / `physiocare.auth`) - skonfiguruj alert hostingu na spike ERROR / 5xx.

## Shared cache (Redis)

Rate limiting DRF korzysta z Django cache. Przy wielu workerach Gunicorn ustaw:

```env
REDIS_URL=redis://127.0.0.1:6379/1
```

Bez Redis używany jest LocMem (OK na 1 worker / lokalnie).

## Monitoring Strumieni SSE

Endpoint `GET /api/v1/me/events/stats/` udostępnia metryki obserwowalności szyny zdarzeń w czasie rzeczywistym:

```json
{
  "engine": "inmemory",
  "active_streams": 3,
  "active_users": 2,
  "total_published": 14,
  "total_dropped": 0,
  "redis_listener_alive": null
}
```

W środowisku produkcyjnym z użyciem Redisa (`engine: "redis"`), pole `redis_listener_alive` określa status żywotności wątku deamona nasłuchującego wiadomości z Pub/Sub.

## Powiązane pliki

| Plik | Rola |
|------|------|
| `backend/physiocare/core/middleware.py` | Timing + request log |
| `backend/physiocare/core/logging_formatters.py` | Formatter JSON |
| `backend/physiocare/core/exceptions.py` | Logowanie błędów API |
| `backend/physiocare/core/media_views.py` | Auth + ownership dla `/media/` |
| `backend/physiocare/physiocare/settings.py` | `LOGGING`, Sentry, Redis cache |
| `backend/tests/core/test_request_timing.py` | Testy nagłówków |
| `backend/tests/core/test_protected_media.py` | Testy ochrony mediów |
