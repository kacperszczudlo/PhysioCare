-- PhysioCare — referencyjny schemat PostgreSQL 16
-- Źródło prawdy po implementacji: migracje Django w backend/
-- Wersja: 0.1 (inicjalizacja dokumentacji)

CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- =============================================================================
-- ENUMS
-- =============================================================================

CREATE TYPE user_role AS ENUM ('PATIENT', 'THERAPIST');
CREATE TYPE episode_status AS ENUM ('IN_PROGRESS', 'COMPLETED_SUCCESS', 'REFERRED', 'INTERRUPTED');
CREATE TYPE visit_status AS ENUM ('SCHEDULED', 'COMPLETED', 'CANCELLED', 'NO_SHOW');
CREATE TYPE body_view_side AS ENUM ('FRONT', 'BACK');
CREATE TYPE media_type AS ENUM ('VIDEO', 'PDF');
CREATE TYPE consent_type AS ENUM (
    'TERMS_REQUIRED',
    'MEDICAL_DATA_REQUIRED',
    'MARKETING_OPTIONAL',
    'RESEARCH_OPTIONAL'
);

-- =============================================================================
-- ACCOUNTS
-- =============================================================================

CREATE TABLE users (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email           VARCHAR(254) NOT NULL UNIQUE,
    password_hash   VARCHAR(128) NOT NULL,
    role            user_role NOT NULL,
    first_name      VARCHAR(100) NOT NULL,
    last_name       VARCHAR(100) NOT NULL,
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE therapist_profiles (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    pwzf_number     VARCHAR(20) NOT NULL UNIQUE,
    phone           VARCHAR(20),
    bio             TEXT,
    courses         JSONB NOT NULL DEFAULT '[]',
    avatar_url      VARCHAR(500),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE patient_profiles (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    therapist_id    UUID NOT NULL REFERENCES therapist_profiles(id) ON DELETE RESTRICT,
    pesel           VARCHAR(11),
    phone           VARCHAR(20),
    avatar_url      VARCHAR(500),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE consents (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    consent_type    consent_type NOT NULL,
    granted         BOOLEAN NOT NULL,
    granted_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (user_id, consent_type)
);

CREATE TABLE notification_preferences (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    pref_key        VARCHAR(50) NOT NULL,
    enabled         BOOLEAN NOT NULL DEFAULT TRUE,
    UNIQUE (user_id, pref_key)
);

-- =============================================================================
-- TREATMENT
-- =============================================================================

CREATE TABLE treatment_episodes (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id      UUID NOT NULL REFERENCES patient_profiles(id) ON DELETE CASCADE,
    icd10_code      VARCHAR(10),
    status          episode_status NOT NULL DEFAULT 'IN_PROGRESS',
    summary_note    TEXT,
    started_at      DATE NOT NULL DEFAULT CURRENT_DATE,
    ended_at        DATE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE body_area_pain (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    episode_id      UUID NOT NULL REFERENCES treatment_episodes(id) ON DELETE CASCADE,
    body_region     VARCHAR(50) NOT NULL,
    view_side       body_view_side NOT NULL,
    vas_score       SMALLINT NOT NULL CHECK (vas_score BETWEEN 0 AND 10),
    pain_character  JSONB NOT NULL DEFAULT '[]',
    recorded_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (episode_id, body_region, view_side)
);

CREATE TABLE visit_notes (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    episode_id      UUID NOT NULL REFERENCES treatment_episodes(id) ON DELETE CASCADE,
    visit_id        UUID,
    content         TEXT NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- =============================================================================
-- SCHEDULING
-- =============================================================================

CREATE TABLE therapy_types (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    therapist_id    UUID NOT NULL REFERENCES therapist_profiles(id) ON DELETE CASCADE,
    name            VARCHAR(100) NOT NULL,
    color_hex       CHAR(7) NOT NULL DEFAULT '#3B82F6',
    duration_min    SMALLINT NOT NULL DEFAULT 45,
    UNIQUE (therapist_id, name)
);

CREATE TABLE visits (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id          UUID NOT NULL REFERENCES patient_profiles(id) ON DELETE CASCADE,
    therapist_id        UUID NOT NULL REFERENCES therapist_profiles(id) ON DELETE CASCADE,
    episode_id          UUID REFERENCES treatment_episodes(id) ON DELETE SET NULL,
    therapy_type_id     UUID NOT NULL REFERENCES therapy_types(id) ON DELETE RESTRICT,
    start_at            TIMESTAMPTZ NOT NULL,
    end_at              TIMESTAMPTZ NOT NULL,
    status              visit_status NOT NULL DEFAULT 'SCHEDULED',
    location_address    VARCHAR(300),
    prep_instructions   TEXT,
    cancel_reason       TEXT,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CHECK (end_at > start_at)
);

ALTER TABLE visit_notes
    ADD CONSTRAINT visit_notes_visit_id_fkey
    FOREIGN KEY (visit_id) REFERENCES visits(id) ON DELETE SET NULL;

CREATE INDEX idx_visits_therapist_start ON visits (therapist_id, start_at);
CREATE INDEX idx_visits_patient_start ON visits (patient_id, start_at);

-- =============================================================================
-- EXERCISES
-- =============================================================================

CREATE TABLE exercise_categories (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name            VARCHAR(80) NOT NULL UNIQUE
);

CREATE TABLE exercises (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    therapist_id    UUID NOT NULL REFERENCES therapist_profiles(id) ON DELETE CASCADE,
    title           VARCHAR(200) NOT NULL,
    media_type      media_type NOT NULL,
    file_url        VARCHAR(500) NOT NULL,
    instruction     TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE exercise_category_map (
    exercise_id     UUID NOT NULL REFERENCES exercises(id) ON DELETE CASCADE,
    category_id     UUID NOT NULL REFERENCES exercise_categories(id) ON DELETE CASCADE,
    PRIMARY KEY (exercise_id, category_id)
);

CREATE TABLE exercise_assignments (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    exercise_id     UUID NOT NULL REFERENCES exercises(id) ON DELETE CASCADE,
    patient_id      UUID NOT NULL REFERENCES patient_profiles(id) ON DELETE CASCADE,
    episode_id      UUID REFERENCES treatment_episodes(id) ON DELETE SET NULL,
    dosage          VARCHAR(100) NOT NULL,
    start_date      DATE NOT NULL,
    end_date        DATE NOT NULL,
    assigned_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CHECK (end_date >= start_date)
);

CREATE TABLE exercise_completions (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    assignment_id   UUID NOT NULL REFERENCES exercise_assignments(id) ON DELETE CASCADE,
    completed_on    DATE NOT NULL DEFAULT CURRENT_DATE,
    done            BOOLEAN NOT NULL DEFAULT TRUE,
    completed_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (assignment_id, completed_on)
);

-- =============================================================================
-- DOCUMENTS
-- =============================================================================

CREATE TABLE medical_documents (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id      UUID NOT NULL REFERENCES patient_profiles(id) ON DELETE CASCADE,
    visit_id        UUID REFERENCES visits(id) ON DELETE SET NULL,
    episode_id      UUID REFERENCES treatment_episodes(id) ON DELETE SET NULL,
    uploaded_by_id  UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    title           VARCHAR(200) NOT NULL,
    file_url        VARCHAR(500) NOT NULL,
    mime_type       VARCHAR(100) NOT NULL DEFAULT 'application/pdf',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- =============================================================================
-- SEED: domyślne kategorie ćwiczeń (opcjonalnie)
-- =============================================================================

INSERT INTO exercise_categories (name) VALUES
    ('Rozciąganie'),
    ('Kończyna dolna'),
    ('Odcinek lędźwiowy'),
    ('Mobilizacja')
ON CONFLICT DO NOTHING;
