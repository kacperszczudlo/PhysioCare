# Wdrożenie - PhysioCare (Faza 6.5)

Przewodnik demo / staging. Lokalny rozwój pozostaje w root `README.md`.

## Architektura wdrożenia

```
[Web: static Vite] --+
                     +--> [Django + DRF + uvicorn ASGI] --> [PostgreSQL]
[Mobile: Expo EAS] --+         |         (^ SSE /api/v1/me/events/)
                               +-- media (volume, TYLKO przez Django /media z JWT)
                               +-- opcjonalnie Redis (throttle cache; później bus SSE)
```

| Komponent | Rekomendacja demo |
|-----------|-------------------|
| Backend + API | Railway / Render / VPS - **uvicorn (ASGI)** gdy włączone live UI |
| PostgreSQL | Managed Postgres (Railway/Render) lub Docker na VPS |
| Redis (opcjonalnie) | Managed Redis - throttle przy >1 workerze; **wymagany** pod SSE multi-worker (na później) |
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
- `EMAIL_*` - SMTP (nie `console` poza lokalnym debugiem); `EMAIL_FROM`, `PASSWORD_RESET_TIMEOUT` (TTL kodu OTP)
- `GOOGLE_CLIENT_IDS` - opcjonalnie, lista OAuth Client ID (Web + Android/iOS) do weryfikacji Sign in with Google
- `LOG_FORMAT=json`
- `MEDIA_ROOT` - trwały volume (**nie** wystawiaj go publicznie w nginx)
- `SENTRY_DSN` - alerty 5xx (patrz [monitoring](monitoring.md))
- `REDIS_URL` - gdy uruchamiasz wiele workerów (throttle; później SSE bus)
- `SSE_HEARTBEAT_SECONDS` - opcjonalnie (domyślnie 20)

### E-mail (weryfikacja konta + reset hasła — kod 6 cyfr)

Lokalnie: `EMAIL_BACKEND=console` (kod w logu Django).

**Demo / praca inżynierska (bez domeny, bez opłat):** Gmail SMTP + [hasło aplikacji](https://myaccount.google.com/apppasswords):

```
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=true
EMAIL_HOST_USER=twoj.gmail@gmail.com
EMAIL_HOST_PASSWORD=<haslo-aplikacji>
EMAIL_FROM=PhysioCare <twoj.gmail@gmail.com>
PASSWORD_RESET_TIMEOUT=1800
```

Rejestracja e-mail+hasło wymaga kodu z wiadomości; Google Sign-In pomija weryfikację. Reset hasła: request → verify (kod) → confirm (`reset_token` + nowe hasło).

Na koniec projektu (własna domena): podmień `EMAIL_*` na Resend/Brevo — logika OTP bez zmian.

### Google Sign-In

Działa na **web (terapeuta)** i **mobile (pacjent)** — login oraz rejestracja z Google.

1. W [Google Cloud Console](https://console.cloud.google.com/) utwórz OAuth Client ID:
   - **Web application** — w Credentials → OAuth client (Web) ustaw **oba** pola:
     - **Authorized JavaScript origins:** `http://localhost:5173`
     - **Authorized redirect URIs:** `http://localhost:5173` (wymagane przez popup Sign-In)
     - Jeśli używasz `http://127.0.0.1:5173`, dodaj ten host osobno do **obu** list
     - Błąd `redirect_uri_mismatch` = brak dokładnego URI z paska adresu w **Authorized redirect URIs**
     - Po zapisie odczekaj 1–2 minuty i twarde odświeżenie (`Ctrl+Shift+R`)
   - **Android** — package `com.physiocare.patient` + SHA-1 debug/release
   - **iOS** — bundle `com.physiocare.patient`
2. Backend (root `.env`):
   ```
   GOOGLE_CLIENT_IDS=<web_id>[,<android_id>][,<ios_id>]
   ```
3. Web (`web/.env.local`):
   ```
   VITE_GOOGLE_CLIENT_ID=<web_id>
   ```
4. Mobile (`mobile/.env`):
   ```
   EXPO_PUBLIC_GOOGLE_WEB_CLIENT_ID=<web_id>
   EXPO_PUBLIC_GOOGLE_IOS_CLIENT_ID=<ios_id>
   ```
5. Mobile wymaga **development build** (nie Expo Go): po dodaniu `@react-native-google-signin/google-signin` przebuduj `npx expo run:android` / `run:ios`.
6. Rejestracja Google: web wymaga PWZFz + oświadczenia; mobile — kod terapeuty + zgody. Login Google łączy istniejące konto po e-mailu.

### Media i pliki medyczne

- Endpoint `GET /media/<path>` wymaga JWT (cookie lub Bearer) oraz ownership (dokument / ćwiczenie / avatar).
- PDF kliniczne w API pacjenta wskazują na `GET /api/v1/{id}/download/` (też z auth).
- **Nie** mapuj `alias /media/ → volume` w nginx - ominiesz autoryzację. Proxy wyłącznie do aplikacji Django.

### Kroki

1. Zainstaluj zależności: `pip install -r backend/requirements.txt` (zawiera `uvicorn`; `gunicorn` tylko jeśli świadomie zostajesz przy WSGI bez SSE)
2. Migracje: `python manage.py migrate` (cwd: `backend/physiocare`)
3. Collectstatic (jeśli serwujesz admin/static): `python manage.py collectstatic --noinput`
4. Uruchom API:
   - **Z live UI (SSE) - rekomendowane na demo:**
     ```bash
     uvicorn physiocare.asgi:application --host 0.0.0.0 --port $PORT
     ```
     Jeden proces ASGI na demo. Przy wielu workerach/instancjach in-memory bus SSE nie fan-outuje między procesami - wtedy Redis (patrz [README - skalowanie](../README.md#na-później-skalowanie)).
   - **Bez SSE / legacy:** `gunicorn physiocare.wsgi:application --bind 0.0.0.0:$PORT`
5. Ustaw healthcheck HTTP na `/api/v1/` (lub dedykowany endpoint)
6. Osobny proces: `python manage.py run_notification_scheduler` (przypomnienia - nie wpinaj w workery API)

### Live UI (SSE) - Nginx / proxy

Dla lokalizacji `/api/v1/me/events/`:

| Ustawienie | Wartość / sens |
|------------|----------------|
| `proxy_buffering` | `off` |
| `proxy_read_timeout` | np. `3600s` (długi stream) |
| `proxy_http_version` | `1.1` |
| `Connection` | pusty / keep-alive zgodnie z reverse proxy |

Web panel: preferuj **same-origin** API (nginx serwuje static + `/api` → uvicorn), żeby `EventSource` wysyłał cookies bez cross-origin. Przy osobnym origin: CORS credentials + konkretny `Access-Control-Allow-Origin` (nie `*`).

Smoke (zalogowany access cookie lub Bearer):

```bash
curl -N -H "Authorization: Bearer <access>" https://<api>/api/v1/me/events/
# oczekuj ramek event: ping
```

### VPS (skrót)

- Nginx → reverse proxy TLS → **uvicorn** (SSE) albo Gunicorn (bez SSE)
- `certbot` dla HTTPS
- systemd unit dla API + Postgres jako usługa systemowa lub Docker Compose
- Redis obok API, gdy wiele workerów
- systemd (lub drugi kontener) dla `run_notification_scheduler`

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
4. Sentry / logi - spadek ERROR

## Web (panel terapeuty)

1. Ustaw `VITE_API_BASE_URL=https://<api-host>/api/v1` **albo** pusty / względny base + reverse proxy same-origin (lepsze pod SSE cookies)
2. `cd web && npm ci && npm run build`
3. Opublikuj katalog `web/dist` jako static site
4. Dopisz origin web do `CORS_ALLOWED_ORIGINS` i `CSRF_TRUSTED_ORIGINS`

Cookie JWT wymagają zgodnego HTTPS i poprawnych CORS credentials. Klient pobiera media przez `fetch` + blob (credentials), nie przez gołe `<img src>` na obcy origin bez cookie. Live Harmonogram/Pulpit: SSE po zalogowaniu (`docs/api.md` - Realtime).

## Mobile (Expo EAS)

1. Konto Expo + `eas-cli`: `npm i -g eas-cli && eas login`
2. W `mobile/`: `eas build:configure`
3. Ustaw `EXPO_PUBLIC_API_BASE_URL` w profilu EAS / `app.config` secrets
4. Preview build: `eas build -p android --profile preview`
5. (Opcjonalnie) OTA: `eas update`

Na urządzeniu fizycznym użyj publicznego URL API (nie `localhost`).
Tokeny natywne: SecureStore. Kanał Expo web używa `localStorage` - nie traktuj go jako produkcyjnego klienta.
Live wizyty/dokumenty/ćwiczenia: SSE z Bearer (foreground); push Expo zostaje na tło.

## Checklist przed demem

- [ ] HTTPS na API i web
- [ ] `DJANGO_DEBUG=false`, `DJANGO_SECURE_COOKIES=true`, `SENTRY_DSN` ustawione
- [ ] `DJANGO_ADMIN_ENABLED=false` lub `DJANGO_ADMIN_ALLOWED_IPS` z Twoim IP
- [ ] API na **uvicorn** (SSE) albo świadomie bez live UI
- [ ] Nginx: `proxy_buffering off` + długi timeout dla `/api/v1/me/events/`
- [ ] `REDIS_URL` gdy wiele workerów
- [ ] Media tylko przez Django (brak publicznego aliasu nginx) - ownership także dla `/media/avatars/`
- [ ] Migracje na czystej bazie staging
- [ ] Konta demo: 1 terapeuta + 1 pacjent z danymi przykładowymi
- [ ] Logi JSON widoczne w panelu hostingu ([monitoring](monitoring.md))
- [ ] Procedura rollback przetestowana raz na staging
- [ ] Build mobile **native** (EAS / Expo Go na telefonie) - **nie** Expo web jako produkcja (localStorage)
- [ ] Checklist live SSE z [e2e-checklist.md](e2e-checklist.md#live-ui-sse) zaliczona

## Alternatywa „tylko laptop”

Jeśli hosting nie jest wymagany na obronie: demo lokalne (Docker Postgres + `runserver` lub `uvicorn` + Vite + Expo) + nagranie / tunel (`ngrok`) dla mobile. `runserver` wystarcza do pokazu SSE przy małej liczbie klientów.
