# Wdrożenie - PhysioCare (Faza 6.5)

Przewodnik demo / staging. Lokalny rozwój pozostaje w root `README.md`.

## Architektura wdrożenia

```
[Web: static Vite] --+
                     +--> [Django + DRF + Gunicorn] --> [PostgreSQL]
[Mobile: Expo EAS] --+         |
                               +-- media (volume, TYLKO przez Django /media z JWT)
                               +-- opcjonalnie Redis (shared throttle cache)
```

| Komponent | Rekomendacja demo |
|-----------|-------------------|
| Backend + API | Railway / Render / VPS (Docker lub Procfile) |
| PostgreSQL | Managed Postgres (Railway/Render) lub Docker na VPS |
| Redis (opcjonalnie) | Managed Redis — wymagany przy >1 workerze Gunicorn |
| Web | Railway static / Cloudflare Pages / Nginx na VPS |
| Mobile | Expo EAS Update + build preview (Android APK) |

## Backend (Railway / VPS)

### Wymagane zmienne

Skopiuj z `.env.example`, w szczególności:

- `DJANGO_SECRET_KEY` (silny, unikalny)
- `DJANGO_DEBUG=false` (domyślne w kodzie; lokalnie ustaw `true` w `.env`)
- `DJANGO_ALLOWED_HOSTS` - host publiczny
- `DJANGO_SECURE_COOKIES=true`, `DJANGO_SECURE_SSL_REDIRECT=true`
- `DJANGO_ADMIN_ENABLED=false` **lub** `DJANGO_ADMIN_ALLOWED_IPS=<twoje IP>` (bez MFA admin jest ryzykiem)
- `POSTGRES_*` / `DATABASE_URL`
- `CORS_ALLOWED_ORIGINS`, `CSRF_TRUSTED_ORIGINS`, `FRONTEND_URL`
- `LOG_FORMAT=json`
- `MEDIA_ROOT` - trwały volume (**nie** wystawiaj go publicznie w nginx)
- `SENTRY_DSN` - alerty 5xx (patrz [monitoring](monitoring.md))
- `REDIS_URL` - gdy uruchamiasz Gunicorn z wieloma workerami

### Media i pliki medyczne

- Endpoint `GET /media/<path>` wymaga JWT (cookie lub Bearer) oraz ownership (dokument / ćwiczenie / avatar).
- PDF kliniczne w API pacjenta wskazują na `GET /api/v1/{id}/download/` (też z auth).
- **Nie** mapuj `alias /media/ → volume` w nginx — ominiesz autoryzację. Proxy wyłącznie do Gunicorn.

### Kroki

1. Zainstaluj zależności: `pip install -r backend/requirements.txt gunicorn`
2. Migracje: `python manage.py migrate` (cwd: `backend/physiocare`)
3. Collectstatic (jeśli serwujesz admin/static): `python manage.py collectstatic --noinput`
4. Uruchom: `gunicorn physiocare.wsgi:application --bind 0.0.0.0:$PORT`
5. Ustaw healthcheck HTTP na `/api/v1/` (lub dedykowany endpoint)

### VPS (skrót)

- Nginx -> reverse proxy TLS -> Gunicorn
- `certbot` dla HTTPS
- systemd unit dla Gunicorn + Postgres jako usługa systemowa lub Docker Compose
- Redis obok API, gdy `WEB_CONCURRENCY` > 1
- systemd (lub drugi kontener) dla `python manage.py run_notification_scheduler` — przypomnienia wizyt i ćwiczeń; nie uruchamiaj tej komendy w każdym workerze Gunicorn

## Rollback (< 5 minut)

Cel: cofnięcie złego deployu bez ręcznej rekonstrukcji bazy (migracje w przód zostawiamy; rollback kodu).

| Hosting | Procedura |
|---------|-----------|
| **Railway / Render** | Panel → Deployments → poprzedni udany deploy → **Rollback** / Redeploy. Sprawdź healthcheck. |
| **VPS + git** | `git fetch && git checkout <previous-sha> && pip install -r backend/requirements.txt && systemctl restart physiocare` (lub docker compose up -d --build). |
| **Web static** | Przywróć poprzedni artefakt `web/dist` (Cloudflare Pages: Instant Rollback; inaczej poprzedni build folder). |
| **Mobile EAS** | `eas update --branch <channel> --message "rollback"` na poprzedni update, albo wskaż poprzedni build w sklepie wewnętrznym. |

Checklist po rollbacku:

1. `curl -fsS https://<api>/api/v1/` → 200/401 (nie 5xx)
2. Logowanie terapeuty + pacjenta
3. `curl -I https://<api>/media/...` bez tokena → 401/403 (nie 200)
4. Sentry / logi — spadek ERROR

## Web (panel terapeuty)

1. Ustaw `VITE_API_BASE_URL=https://<api-host>/api/v1`
2. `cd web && npm ci && npm run build`
3. Opublikuj katalog `web/dist` jako static site
4. Dopisz origin web do `CORS_ALLOWED_ORIGINS` i `CSRF_TRUSTED_ORIGINS`

Cookie JWT wymagają zgodnego HTTPS i poprawnych CORS credentials. Klient pobiera media przez `fetch` + blob (credentials), nie przez gołe `<img src>` na obcy origin bez cookie.

## Mobile (Expo EAS)

1. Konto Expo + `eas-cli`: `npm i -g eas-cli && eas login`
2. W `mobile/`: `eas build:configure`
3. Ustaw `EXPO_PUBLIC_API_BASE_URL` w profilu EAS / `app.config` secrets
4. Preview build: `eas build -p android --profile preview`
5. (Opcjonalnie) OTA: `eas update`

Na urządzeniu fizycznym użyj publicznego URL API (nie `localhost`).
Tokeny natywne: SecureStore. Kanał Expo web używa `localStorage` — nie traktuj go jako produkcyjnego klienta.

## Checklist przed demem

- [ ] HTTPS na API i web
- [ ] `DJANGO_DEBUG=false`, `DJANGO_SECURE_COOKIES=true`, `SENTRY_DSN` ustawione
- [ ] `DJANGO_ADMIN_ENABLED=false` lub `DJANGO_ADMIN_ALLOWED_IPS` z Twoim IP
- [ ] `REDIS_URL` gdy Gunicorn ma >1 worker
- [ ] Media tylko przez Django (brak publicznego aliasu nginx) — ownership także dla `/media/avatars/`
- [ ] Migracje na czystej bazie staging
- [ ] Konta demo: 1 terapeuta + 1 pacjent z danymi przykładowymi
- [ ] Logi JSON widoczne w panelu hostingu ([monitoring](monitoring.md))
- [ ] Procedura rollback przetestowana raz na staging
- [ ] Build mobile **native** (EAS / Expo Go na telefonie) — **nie** Expo web jako produkcja (localStorage)

## Alternatywa „tylko laptop”

Jeśli hosting nie jest wymagany na obronie: demo lokalne (Docker Postgres + `runserver` + Vite + Expo) + nagranie / tunel (`ngrok`) dla mobile.
