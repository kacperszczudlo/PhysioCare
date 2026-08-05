# Konspekt prezentacji — PhysioCare

Slajdy + demo live (Faza 6.7). Czas orientacyjny: 10–12 minut.

## Slajdy (propozycja 10)

1. **Tytuł** — PhysioCare, autor, uczelnia, rok
2. **Problem** — rozproszona dokumentacja wizyt, brak compliance ćwiczeń domowych
3. **Cel i zakres** — web (terapeuta) + mobile (pacjent) + wspólne REST API
4. **Architektura** — diagram kontenerów (`docs/diagrams/architecture.drawio`)
5. **Model danych** — ERD (epizod, wizyta, ćwiczenia, zgody)
6. **API i bezpieczeństwo** — JWT, role, throttling, envelope błędów
7. **Aplikacje klienckie** — kluczowe ekrany web + mobile (screenshoty)
8. **Jakość** — pytest, Ruff, ESLint/Prettier, monitoring (`X-Request-ID`, latency)
9. **Demo** — przejście ścieżki krytycznej (patrz poniżej)
10. **Podsumowanie** — osiągnięcia, ograniczenia, możliwe rozszerzenia

## Demo live (3–4 min)

Kolejność:

1. Logowanie terapeuty (web) → harmonogram → otwarcie karty pacjenta
2. Przypisanie ćwiczenia
3. Logowanie pacjenta (mobile) → pulpit → oznaczenie wykonania
4. (Opcjonalnie) log JSON w terminalu backendu z `request_id`

Backup: nagranie ekranu / Postman smoke, gdy sieć lub emulator zawiedzie.

## Materiały

| Plik | Użycie |
|------|--------|
| `docs/diagrams/*.drawio` | Slajdy architektury / ERD / UC |
| `docs/e2e-checklist.md` | Scenariusz próby generalnej |
| `docs/monitoring.md` | Slajd jakości / ops |
| `docs/deployment.md` | Pytania o hosting |
| Screenshoty (katalog `docs/screenshots/` — do uzupełnienia) | Slajd UI |

## Pytania — szybkie odpowiedzi

- **Dlaczego monorepo?** Wspólny kontrakt API, jedna historia Git, łatwiejsza synchronizacja typów.
- **Dlaczego JWT w cookie (web) i Bearer (mobile)?** XSS vs natywne SecureStore; ten sam backend.
- **Co z RODO?** Zgody przy rejestracji pacjenta, endpointy privacy, minimalizacja danych w logach (`user_id`, bez haseł).
