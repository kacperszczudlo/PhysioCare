# Wdrożenie - PhysioCare (Faza 6.5)

Przewodnik demo / staging. Lokalny rozwój pozostaje w root `README.md`.

## Architektura wdrożenia

```
[Web: static Vite] ──┐
                     ├──► [Django + DRF + Gunicorn] ──► [PostgreSQL]
[Mobile: Expo EAS] ──┘         │
                               └── media (volume / object storage)
```

| Komponent | Rekomendacja demo |
|-----------|-------------------|
| Backend + API | Railway / Render / VPS (Docker lub Procfile) |
| PostgreSQL | Managed Postgres (Railway/Render) lub Docker na VPS |
| Web | Railway static / Cloudflare Pages / Nginx na VPS |
| Mobile | Expo EAS Update + build preview (Android APK) |

## Backend (Railway / VPS)

### Wymagane zmienne

Skopiuj z `.env.example`, w szczególności:

- `DJANGO_SECRET_KEY` (silny, unikalny)
- `DJANGO_DEBUG=false`
- `DJANGO_ALLOWED_HOSTS` - host publiczny
- `DJANGO_SECURE_COOKIES=true`, `DJANGO_SECURE_SSL_REDIRECT=true`
- `POSTGRES_*` / `DATABASE_URL`
- `CORS_ALLOWED_ORIGINS`, `CSRF_TRUSTED_ORIGINS`, `FRONTEND_URL`
- `LOG_FORMAT=json`
- `MEDIA_ROOT` - trwały volume

### Kroki

1. Zainstaluj zależności: `pip install -r backend/requirements.txt gunicorn`
2. Migracje: `python manage.py migrate` (cwd: `backend/physiocare`)
3. Collectstatic (jeśli serwujesz admin/static): `python manage.py collectstatic --noinput`
4. Uruchom: `gunicorn physiocare.wsgi:application --bind 0.0.0.0:$PORT`
5. Ustaw healthcheck HTTP na `/api/v1/` (lub dedykowany endpoint)

### VPS (skrót)

- Nginx → reverse proxy TLS → Gunicorn
- `certbot` dla HTTPS
- systemd unit dla Gunicorn + Postgres jako usługa systemowa lub Docker Compose

## Web (panel terapeuty)

1. Ustaw `VITE_API_BASE_URL=https://<api-host>/api/v1`
2. `cd web && npm ci && npm run build`
3. Opublikuj katalog `web/dist` jako static site
4. Dopisz origin web do `CORS_ALLOWED_ORIGINS` i `CSRF_TRUSTED_ORIGINS`

Cookie JWT wymagają zgodnego HTTPS i poprawnych CORS credentials.

## Mobile (Expo EAS)

1. Konto Expo + `eas-cli`: `npm i -g eas-cli && eas login`
2. W `mobile/`: `eas build:configure`
3. Ustaw `EXPO_PUBLIC_API_BASE_URL` w profilu EAS / `app.config` secrets
4. Preview build: `eas build -p android --profile preview`
5. (Opcjonalnie) OTA: `eas update`

Na urządzeniu fizycznym użyj publicznego URL API (nie `localhost`).

## Checklist przed demem

- [ ] HTTPS na API i web
- [ ] Migracje na czystej bazie staging
- [ ] Konta demo: 1 terapeuta + 1 pacjent z danymi przykładowymi
- [ ] Logi JSON widoczne w panelu hostingu ([monitoring](monitoring.md))
- [ ] Build mobile zainstalowany lub Expo Go + update channel

## Alternatywa „tylko laptop”

Jeśli hosting nie jest wymagany na obronie: demo lokalne (Docker Postgres + `runserver` + Vite + Expo) + nagranie / tunel (`ngrok`) dla mobile.
