# Konspekt prezentacji - PhysioCare

Slajdy i pokaz na żywo (Faza 6.7). Ramowy czas: 10-12 minut.

## Slajdy (propozycja 10)

1. **Tytuł** - PhysioCare, autor, uczelnia, rok
2. **Problem** - rozrzucona dokumentacja wizyt i brak śladu ćwiczeń domowych
3. **Cel i zakres** - web (terapeuta), mobile (pacjent), wspólne REST API
4. **Architektura** - diagram kontenerów (`docs/diagrams/architecture.drawio`)
5. **Model danych** - ERD (epizod, wizyta, ćwiczenia, zgody)
6. **API i bezpieczeństwo** - JWT, role, throttle, envelope błędów, blacklist refresh
7. **Aplikacje klienckie** - kluczowe ekrany web + mobile (screenshoty)
8. **Jakość** - pytest, Ruff, ESLint/Prettier, monitoring (`X-Request-ID`, latency)
9. **Demo** - ścieżka krytyczna (niżej)
10. **Zamknięcie** - co powstało, czego nie ma, możliwe dalsze kroki

## Demo live (3-4 min)

Kolejność:

1. Wejście terapeuty (web) → kalendarz → karta pacjenta
2. Przypisanie ćwiczenia
3. Wejście pacjenta (mobile) → pulpit → oznaczenie wykonania
4. (Opcjonalnie) log JSON backendu z `request_id`

Rezerwa: nagranie ekranu albo smoke w Postmanie, gdy padnie sieć albo emulator.

## Materiały

| Plik | Użycie |
|------|--------|
| `docs/diagrams/*.drawio` | Slajdy architektury / ERD / UC |
| `docs/e2e-checklist.md` | Scenariusz próby generalnej |
| `docs/monitoring.md` | Slajd jakości / ops |
| `docs/deployment.md` | Pytania o hosting |
| Screenshoty (katalog `docs/screenshots/` - do uzupełnienia) | Slajd UI |

## Pytania - szybkie odpowiedzi

- **Dlaczego monorepo?** Jeden kontrakt API, jedna historia Git, prościej trzymać typy w ryzach.
- **Dlaczego JWT w cookie (web) i Bearer (mobile)?** Ograniczenie XSS versus natywny SecureStore; ten sam backend.
- **Co z RODO?** Zgody przy rejestracji pacjenta, eksport i wniosek o usunięcie na API, w logach `user_id` bez haseł.
