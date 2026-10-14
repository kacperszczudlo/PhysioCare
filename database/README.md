# Schemat Bazy Danych — PhysioCare

Katalog zawiera deklarację i zrzut struktury relacyjnej bazy danych PostgreSQL dla systemu PhysioCare.

## Zawartość katalogu

- **`schema.sql`**: Kompletny zrzut DDL (Data Definition Language) obiektów bazy danych wygenerowany na podstawie migracji Django (PostgreSQL 16+).

## Kluczowe mechanizmy bazy danych

1. **Więzy wykluczenia czasowego (`btree_gist`):**
   - Rozszerzenie PostgreSQL `btree_gist` pozwala na definiowanie ograniczeń `ExclusionConstraint` na przedziałach czasowych `[start_at, end_at)` wizyt oraz przypisań ćwiczeń.
   - Gwarantuje brak nakładających się terminów (eliminacja problemu *double-booking*) na poziomie silnika relacyjnego, niezależnie od współbieżności transakcji.

2. **Integralność danych i więzy sprawdzające (`CheckConstraint`):**
   - `chk_review_rating_1_to_5`: Wymusza ocenę recenzji wyłącznie w zakresie liczb całkowitych 1–5 na tabeli `therapist_reviews`.
   - `chk_body_pain_vas_score`: Skala bólu VAS ściśle w przedziale 0–10 na tabeli `body_area_pain`.
   - `chk_visits_end_after_start`: Zakończenie wizyty musi być późniejsze niż jej rozpoczęcie.
   - `chk_exercise_assignment_dates`: Data końcowa przypisania ćwiczenia nie może poprzedzać daty początkowej.

3. **Optymalizacja zapytań i indeksacja (`db_index=True`):**
   - Wszystkie tabele dziedziczące po bazowym `TimestampedModel` (`patient_profiles`, `therapist_profiles`, `visits`, `treatment_episodes`, `therapist_reviews`, `medical_documents`, `exercises` itp.) posiadają dedykowany indeks B-drzewa na kolumnie `created_at`.
   - Zapewnia to natychmiastowe sortowanie chronologiczne i wsparcie deterministycznej paginacji bez konieczności kosztownego przeszukiwania sekwencyjnego (*Seq Scan*).

4. **Szyfrowanie at-rest (RODO Art. 9 / Fernet AES-128-CBC):**
   - Wrażliwe kolumny medyczne (`pesel`, `functional_diagnosis`, `content` notatek, `justification` zaleceń, `notes` wyrobów medycznych, sekretny klucz TOTP `secret_key`) są przechowywane w bazie wyłącznie w formie zaszyfrowanego szyfrogramu (`gAAAAA...`).

## Aktualizacja schematu

Struktura bazodanowa w projekcie zarządzana jest wyłącznie za pośrednictwem migracji Django (`python manage.py makemigrations` i `python manage.py migrate`). Aby zaktualizować plik `database/schema.sql` na podstawie bazy PostgreSQL, uruchom skrypt:
```bash
python scripts/sync_schema_sql.py
```
