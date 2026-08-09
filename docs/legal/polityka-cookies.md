# Polityka plików cookies i technologii w urządzeniu końcowym — PhysioCare

**Wersja:** 1.0  
**Data:** 8 sierpnia 2026 r.  
**Powiązana z:** [Polityką prywatności](./polityka-prywatnosci.md)

## 1. Cel dokumentu

Niniejsza Polityka wyjaśnia, w jaki sposób PhysioCare przechowuje informacje lub uzyskuje dostęp do informacji w telekomunikacyjnym urządzeniu końcowym użytkownika (przeglądarka / aplikacja mobilna), zgodnie z:

- art. 399–400 **Prawa komunikacji elektronicznej (PKE)**,
- wymogami zgody wynikającymi z **RODO** (gdy technologia nie jest niezbędna),
- wytycznymi EROD dotyczącymi zgody (m.in. wykluczenie zgody domniemanej i „cookie walls”).

## 2. Podział technologii

### 2.1. Niezbędne (wyjątek od uprzedniej zgody na tracking)

Dozwolone bez dodatkowej zgody marketingowej / analitycznej, gdy są absolutnie niezbędne do świadczenia usługi zażądanej przez użytkownika lub do transmisji komunikatu:

| Nazwa | Typ | Cel | Czas życia |
|-------|-----|-----|------------|
| `access_token` | cookie httpOnly | Utrzymanie sesji zalogowanego użytkownika (JWT) | krótki (domyślnie ~15 min) |
| `refresh_token` | cookie httpOnly | Odświeżenie sesji | domyślnie do ~7 dni, z rotacją |
| Tokeny w SecureStore | magazyn aplikacji mobilnej | Analog sesji poza przeglądarką | do wylogowania / wygaśnięcia |

Cookies sesji ustawiane są z flagami ograniczającymi dostęp skryptów stron trzecich (`httpOnly`), a w produkcji — `Secure` oraz `SameSite=Lax` (lub równoważna konfiguracja bezpieczeństwa).

### 2.2. Analityczne, reklamowe, preferencyjne śledzące

**Obecnie nieużywane.** PhysioCare nie instaluje takich technologii.  
Gdyby miały zostać dodane:

1. domyślnie będą **wyłączone**,
2. pojawią się równorzędne opcje „Akceptuj” / „Odrzuć” (parytet wizualny),
3. zgoda będzie granularna (osobno cele),
4. SDK zewnętrzne uruchomią się **dopiero po** potwierdzonej zgodzie (inicjalizacja asynchroniczna),
5. wycofanie zgody będzie dostępne w ustawieniach / stopce bez „labiryntu”.

## 3. Zarządzanie

- **Web:** wylogowanie usuwa / unieważnia sesję; przeglądarka pozwala też usuwać cookies w ustawieniach systemowych.
- **Mobile:** wylogowanie czyści tokeny z bezpiecznego magazynu.
- **Zgody opcjonalne RODO** (marketing / badania): ustawienia aplikacji mobilnej pacjenta — niezależne od cookies niezbędnych.

## 4. Więcej informacji

Pełny opis przetwarzania danych osobowych: [Polityka prywatności](./polityka-prywatnosci.md) oraz strona `/privacy`.
