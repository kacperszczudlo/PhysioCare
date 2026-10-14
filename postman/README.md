# Kolekcja Postman — PhysioCare

Katalog zawiera oficjalną kolekcję testową REST API oraz definicję środowiska dla narzędzia Postman Desktop / Postman CLI (Newman).

## Struktura katalogu

- **`collections/PhysioCare.json`**: Główna kolekcja żądań HTTP obejmująca pełen cykl życia aplikacji (onboarding, autoryzacja JWT/2FA, epizody leczenia, mapa bólu VAS, harmonogram wizyt, zadania domowe HEP, moduły RODO i administracji).
- **`environments/PhysioCare.postman_environment.json`**: Domyślne zmienne środowiskowe dla testów lokalnych (`http://localhost:8000/api/v1`).

## Szybki start

1. Otwórz Postman Desktop.
2. Zaimportuj pliki:
   - `postman/collections/PhysioCare.json`
   - `postman/environments/PhysioCare.postman_environment.json`
3. Wybierz środowisko **PhysioCare Local**.
4. Włącz **Cookie Jar** dla domeny `localhost`.
5. Uruchom folder **`00 Setup - Auth & seed`** jako pierwszy (rejestracja i logowanie personelu oraz pacjentów).

Szczegółowy przewodnik po scenariuszach testowych i macierzy przypadków użycia (UC-01 – UC-29) znajduje się w dokumencie [`docs/postman-testing.md`](../docs/postman-testing.md).
