# Konspekt prezentacji dyplomowej - PhysioCare

Plan wystąpienia i pokazu na żywo. Ramowy czas wystąpienia: 10–12 minut.

## Slajdy (Struktura prezentacji)

1. **Strona tytułowa** – Tytuł pracy, autor, kierunek, uczelnia, rok akademicki.
2. **Sformułowanie problemu** – Wyzwania organizacji dokumentacji fizjoterapeutycznej i kontroli zaleceń domowych.
3. **Cel i zakres projektu** – Zintegrowany system trójwarstwowy: panel WWW, aplikacja mobilna, centralny backend REST.
4. **Architektura systemu** – Schemat kontenerów (`docs/diagrams/architecture.drawio`) oraz protokół SSE.
5. **Model danych** – Schemat ERD (epizody leczenia, wizyty, plan ćwiczeń, zgody RODO).
6. **API i bezpieczeństwo** – Bezstanowy JWT, mechanizm 2FA, ochrona PESEL/notatek (AES-128 Fernet), rate limiting.
7. **Interfejsy użytkownika** – Prezentacja kluczowych ekranów panelu fizjoterapeuty i aplikacji pacjenta.
8. **Jakość oprogramowania i monitoring** – Testy jednostkowe/integracyjne, logi strukturalne JSON (`X-Request-ID`), obsługa błędów.
9. **Pokaz na żywo (Demo)** – Przebieg ścieżki krytycznej (opis poniżej).
10. **Podsumowanie i wnioski** – Wnioski końcowe, osiągnięte cele oraz kierunki rozwoju systemu.

## Pokaz na żywo (Demo live: 3–4 min)

Kolejność prezentacji:

1. **Panel fizjoterapeuty (Web):** Logowanie, prezentacja harmonogramu oraz otwarcie karty pacjenta z mapą bólu VAS.
2. **Przypisanie ćwiczenia:** Wybór z bazy ćwiczeń, ustalenie dawkowania i przydzielenie pacjentowi.
3. **Aplikacja pacjenta (Mobile):** Odbiór powiadomienia w czasie rzeczywistym (SSE), przejście do zaleceń na dziś i oznaczenie wykonania (compliance).
4. **Weryfikacja w logach:** Prezentacja wpisu logu strukturalnego JSON z nagłówkiem `X-Request-ID`.

*Rezerwa techniczna:* Material wideo prezentujący działanie systemu przygotowany na przypadek awarii sieci.

## Materiały źródłowe

| Plik / Zasób | Zastosowanie w prezentacji |
| :--- | :--- |
| `docs/diagrams/*.drawio` | Slajdy architektury, schematu ERD oraz przypadek użycia |
| `docs/monitoring.md` | Slajd poświęcony obserwowalności i jakości |
| `docs/deployment.md` | Odpowiedzi na pytania dotyczące infrastruktury |
| `docs/screenshots/` | Zrzuty ekranu interfejsów klienckich |

## Przygotowane odpowiedzi na pytania komisji

- **Dlaczego architektura monorepo?** Wspólny kontrakt REST API, jednolity rejestr typów oraz łatwiejsza kontrola spójności wersji.
- **Dlaczego JWT w cookie (Web) i Bearer (Mobile)?** Ochrona przed atakami XSS w przeglądarce przy jednoczesnym wykorzystaniu natywnego magazynu `SecureStore` w systemach mobilnych.
- **Jak obsłużono wymogi RODO?** Dwuetapowa akceptacja zgód przy rejestracji, prawa DSAR (eksport i anonimizacja konta) oraz szyfrowanie danych medycznych at-rest.
