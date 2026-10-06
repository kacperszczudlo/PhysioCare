# Wdrożenie i Architektura CDN - PhysioCare

Niniejszy dokument opisuje architekturę wdrożeniową systemu PhysioCare z uwzględnieniem celowanego wdrożenia sieci dostarczania treści (**CDN - Content Delivery Network**) oraz reguł ochrony danych medycznych.

---

## 1. Architektura wdrożenia z podziałem na warstwy

```
+---------------------------------------------------------------------------------+
|                                 UŻYTKOWNIK                                      |
+---------------------------------------------------------------------------------+
          |                                                      |
          v (Panel Web - Terapeuta)                              v (Aplikacja Mobile - Pacjent)
+-----------------------------------------+            +----------------------------------+
|      CDN Edge (Cloudflare Pages)        |            |   Klient Expo (Android / iOS)    |
| - Statyczny build React + Vite          |            | - Kompilacja natywna (EAS APK)   |
| - _headers (1 rok immutable dla /assets)|            | - Aktualizacje OTA (EAS Update)  |
| - _redirects (SPA client fallback)      |            +----------------------------------+
+-----------------------------------------+                              |
          |                                                              |
          | Zapytania API / Autoryzowane Media                           |
          +-------------------------------+------------------------------+
                                          |
                                          v
+---------------------------------------------------------------------------------+
|                   Cloudflare Reverse Proxy / Edge Shield                        |
| - Ochrona DDoS, Web Application Firewall (WAF)                                  |
| - Automatyczne wymuszenie TLS 1.3 / HTTPS                                       |
| - Reguła: CACHE BYPASS dla /api/* oraz /media/*                                 |
| - Reguła: Proxy Buffering OFF dla SSE (/api/v1/me/events/)                      |
+---------------------------------------------------------------------------------+
                                          |
                                          v
+---------------------------------------------------------------------------------+
|                         Serwer Aplikacji (Origin)                               |
|                     Uvicorn (ASGI) / Gunicorn + Django                          |
| - REST API z autoryzacją JWT i rolami (THERAPIST / PATIENT)                     |
| - Kanał SSE: aiter_sse_frames (/api/v1/me/events/)                              |
| - Chronione media (/media/*): weryfikacja praw + Cache-Control: private, no-store|
| - Django staticfiles: STATIC_ROOT zebrane przez collectstatic                   |
+---------------------------------------------------------------------------------+
          |                                                      |
          v                                                      v
+-----------------------------------------+            +----------------------------------+
|          Baza PostgreSQL 16             |            |    Wolumen dyskowy / S3 Bucket   |
|  Szyfrowanie Fernet (PESEL, notatki)    |            |   Chronione pliki i załączniki   |
+-----------------------------------------+            +----------------------------------+
```

---

## 2. Celowane wdrożenie CDN – komponenty

### A. Frontend panelu terapeuty (`web/`) – Cloudflare Pages
Panel webowy jest aplikacją Single Page Application (SPA) opartą o React 19 i Vite. Wszystkie zasoby statyczne serwowane są bezpośrednio z serwerów brzegowych (Edge Nodes):
- **Skompilowane zasoby (`/assets/*`):** Posiadają unikalne skróty w nazwach plików generowane podczas budowania (`[name]-[hash].js`, `[name]-[hash].css`). W pliku `web/public/_headers` skonfigurowano nagłówek `Cache-Control: public, max-age=31536000, immutable`. Dzięki temu serwery brzegowe CDN oraz przeglądarki pobierają dany plik tylko raz, co drastycznie skraca czas ładowania panelu gabinetu.
- **Plik główny (`/index.html`):** Posiada nagłówek `Cache-Control: public, max-age=0, must-revalidate`. Zapewnia to natychmiastowe unieważnienie pamięci podręcznej i natychmiastowy dostęp do nowo wdrożonej wersji po każdym kolejnym release.
- **Routing SPA (`_redirects`):** Plik `web/public/_redirects` zawiera regułę `/* /index.html 200`, która przekierowuje wszystkie ścieżki routingu po stronie klienta do głównego szablonu HTML, zapobiegając błędom 404 HTTP na krawędzi CDN.

### B. Serwer Django REST API – Origin i ochrona danych medycznych
- **Ścisły zakaz buforowania danych medycznych:** Zasoby kliniczne w ścieżkach `/media/*` oraz endpoint pobierania dokumentów medycznych `GET /api/v1/documents/<uuid>/download/` zwracają nagłówki:
  ```http
  Cache-Control: private, no-store
  X-Content-Type-Options: nosniff
  ```
  Zgodnie z wymogami RODO i bezpieczeństwa dokumentacji medycznej żaden publiczny serwer proxy ani węzeł pośredniczący CDN nie ma prawa buforować kart pacjenta, skierowań ani danych osobowych.
- **Zbieranie statyków Django (`STATIC_ROOT`):** W `settings.py` zdefiniowano `STATIC_ROOT = ROOT_DIR / 'backend' / 'staticfiles'`, co pozwala na wykonanie polecenia `python manage.py collectstatic --noinput` w procesie budowania obrazu lub deploymentu panelu administracyjnego.

---

## 3. Konfiguracja reguł Cloudflare (Edge Rules)

W przypadku podpięcia domeny głównej pod Cloudflare, w panelu zarządzania należy skonfigurować następujące reguły:

### Reguła 1: Wyłączenie buforowania dla API i Mediów (Cache Rule: Bypass)
- **Warunek dopasowania:** `URI Path starts with "/api/"` LUB `URI Path starts with "/media/"`
- **Działanie:** 
  - **Cache eligibility:** *Bypass cache*
- **Uzasadnienie:** Zapobiega buforowaniu dynamicznych odpowiedzi REST oraz gwarantuje sprawdzanie uprawnień JWT i ownership dla każdego pliku medycznego.

### Reguła 2: Bezpieczeństwo kanału czasu rzeczywistego SSE (`/api/v1/me/events/`)
- **Warunek dopasowania:** `URI Path equals "/api/v1/me/events/"`
- **Działanie:**
  - Wyłączenie buforowania odpowiedzi (*Proxy Buffering: Off*).
  - Wyłączenie optymalizacji Rocket Loader, Auto Minify oraz Email Obfuscation (zapobiega modyfikowaniu strumienia chunked text/event-stream).

---

## 4. Procedura wdrożenia krok po kroku

### Krok 1: Wdrożenie frontendu na Cloudflare Pages
1. Połącz repozytorium GitHub w panelu Cloudflare Pages.
2. Skonfiguruj parametry budowania:
   - **Framework preset:** `Vite`
   - **Root directory:** `web`
   - **Build command:** `npm run build`
   - **Build output directory:** `dist`
3. Dodaj zmienną środowiskową:
   - `VITE_API_BASE_URL` = adres publiczny backendu (np. `https://api.twojadomena.pl/api/v1`).

### Krok 2: Wdrożenie backendu (VPS / Docker / Railway)
1. Skonfiguruj zmienne środowiskowe z `.env.example`.
2. Uruchom migracje bazy danych:
   ```bash
   python manage.py migrate
   ```
3. Zbierz pliki statyczne Django:
   ```bash
   python manage.py collectstatic --noinput
   ```
4. Uruchom serwer aplikacji za pomocą serwera ASGI obsługującego SSE:
   ```bash
   uvicorn physiocare.asgi:application --host 0.0.0.0 --port 8000
   ```
