# Plan Wdrożenia Architektury Django & DRF (HackSoft / CQRS / API as a Product)

> **Dla wykonawców agentowych:** WYMAGANY SUB-SKILL: Użyj `superpowers:executing-plans` (lub `superpowers:subagent-driven-development`) do wdrożenia tego planu zadanie po zadaniu. Kroki używają składni checkboxów (`- [ ]`) do śledzenia postępów.

**Cel:** Przeprowadzić ukierunkowaną refaktoryzację architektury backendu PhysioCare zgodnie ze standardem `/django-drf-architecture` (HackSoft Styleguide, CQRS: Services & Selectors, API as a Product, integralność DB PostgreSQL i prewencja $N+1$).

**Architektura:** Wprowadzenie ścisłej separacji odpowiedzialności: widoki (`APIView`) jako cienka warstwa translacyjna HTTP, `services.py` jako wyłączny punkt mutacji stanu (`@transaction.atomic`, `full_clean()`, brak `request`), `selectors.py` dla optymalizowanego odczytu (`select_related`, `prefetch_related`), eliminacja sygnałów Django (`signals.py`), twarde więzy w bazie (`CheckConstraint`) oraz formalny kontrakt OpenAPI 3.0 (`drf-spectacular`).

**Stos technologiczny:** Python 3.12, Django 6.0, Django REST Framework 3.17, drf-spectacular 0.28+, PostgreSQL, pytest-django, ruff.

**Dokument źródłowy / Standard:** `C:\Users\kacpe\.gemini\config\skills\django-drf-architecture\SKILL.md`

---

## Global Constraints

- **Python / Django versions:** Python 3.12+, Django 6.0.x, DRF 3.17.x.
- **Zakaz obiektów `request` w serwisach:** Funkcje w `services.py` przyjmują wyłącznie prymitywy, dataclasses lub encje ORM; nigdy `HttpRequest` lub `Request`.
- **Jawna walidacja w serwisach:** Każda mutacja modelu w serwisie musi wywoływać `instance.full_clean()` przed `instance.save()`.
- **Transakcyjność:** Wszystkie operacje modyfikujące więcej niż 1 tabelę lub wywołujące powiadomienia muszą być objęte `@transaction.atomic`.
- **Zakaz sygnałów Django:** Wszelkie efekty uboczne (denormalizacja, SSE, powiadomienia) muszą być wywoływane jawnie w warstwie `services.py`.
- **Zakaz zapytań ORM w `@property`:** Właściwości modeli mogą wykonywać wyłącznie operacje in-memory na załadowanych polach; brak filtrów ani zapytań w pętli.
- **Kompatybilność wsteczna API:** Brak zmian w kontraktach URL (`/api/v1/...`) ani strukturach odpowiedzi JSON dla aplikacji frontendowej (Vite SPA) i mobilnej (React Native/Expo). Wszystkie 37 testów reviews i suite testowy muszą pozostać w 100% zielone.

---

## Review Focus

1. **Denormalizacja ocen po usunięciu `signals.py`:** Upewnić się, że po usunięciu `reviews/signals.py`, serwisy `review_create_service`, `review_edit_service` oraz `review_delete_service` bezwzględnie aktualizują `therapist.rating_avg` i `therapist.rating_count`.
2. **Zachowanie transakcyjności i rollback przy błędach kolizji wizyt:** W `scheduling/services.py` obsługa `IntegrityError` (`exclude_overlapping_visits`) musi precyzyjnie mapować się na `ValidationError` DRF z polem `start_at`.
3. **Paginacja i wydajność zapytań:** W selektorach `reviews/selectors.py` i `scheduling/selectors.py` sprawdzić, czy `select_related` pobiera klucze obce (`patient__user`, `therapist__user`, `therapy_type`), eliminując zapytania $N+1$.
4. **Wielodostępność i BOLA/IDOR:** Sprawdzić, czy selektory i serwisy wymuszają uprawnienia podmiotowe (np. `patient_id` z kontekstu autoryzacji), zapobiegając nieautoryzowanym manipulacjom danymi innych użytkowników.
5. **Integralność bazy PostgreSQL:** Sprawdzić, czy nowo dodany `CheckConstraint` dla ocen `1 <= rating <= 5` oraz indeks `db_index=True` na `created_at` migrują się gładko bez blokowania bazy ani naruszenia istniejących danych.

---

## Zadania do Wykonania

### Task 1: Konfiguracja API as a Product (OpenAPI 3.0 via drf-spectacular) & Tooling
### Task 2: Integralność Bazy Danych i Modele: Indeksowanie created_at i CheckConstraint
### Task 3: Eliminacja zapytań ORM z @property (PatientProfile.therapist N+1 fix)
### Task 4: Moduł Reviews: Warstwa Selektorów (reviews/selectors.py)
### Task 5: Moduł Reviews: Warstwa Usług (reviews/services.py) i Eliminacja signals.py
### Task 6: Moduł Reviews: Refaktoryzacja Widoków na Serwisy i Selektory (reviews/views.py)
### Task 7: Domena Scheduling: Warstwa Selektorów (scheduling/selectors.py)
### Task 8: Domena Scheduling: Warstwa Usług (scheduling/services.py)
### Task 9: Domena Scheduling: Odchudzenie Widoków (scheduling/views.py)
### Task 10: Weryfikacja Końcowa, Jakość Kodu (Ruff) i Zgodność Architektury
