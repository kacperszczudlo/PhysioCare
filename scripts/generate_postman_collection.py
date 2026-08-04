#!/usr/bin/env python3
"""Generate PhysioCare Postman Collection v2.1 from backend contract."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_COLLECTION = ROOT / "docs" / "postman" / "PhysioCare.json"
OUT_ENV = ROOT / "docs" / "postman" / "PhysioCare.postman_environment.json"
OUT_COPY = ROOT / "postman" / "collections" / "PhysioCare.json"


def req(
    name: str,
    method: str,
    path: str,
    *,
    body: dict | None = None,
    raw: str | None = None,
    query: list[tuple[str, str]] | None = None,
    description: str = "",
    tests: str = "",
    auth: str | None = "bearer",
    formdata: list[dict] | None = None,
    headers: list[dict] | None = None,
) -> dict:
    url = {
        "raw": "{{baseUrl}}" + path + (
            ("?" + "&".join(f"{k}={v}" for k, v in query)) if query else ""
        ),
        "host": ["{{baseUrl}}"],
        "path": [p for p in path.strip("/").split("/") if p],
    }
    if query:
        url["query"] = [{"key": k, "value": v} for k, v in query]

    item: dict = {
        "name": name,
        "request": {
            "method": method,
            "header": headers or [],
            "url": url,
            "description": description,
        },
    }

    if auth == "bearer":
        item["request"]["auth"] = {
            "type": "bearer",
            "bearer": [{"key": "token", "value": "{{access_token}}", "type": "string"}],
        }
    elif auth == "none":
        item["request"]["auth"] = {"type": "noauth"}

    if formdata is not None:
        item["request"]["body"] = {"mode": "formdata", "formdata": formdata}
        item["request"]["header"] = [
            h for h in item["request"]["header"] if h.get("key", "").lower() != "content-type"
        ]
    elif body is not None or raw is not None:
        item["request"]["header"] = [
            {"key": "Content-Type", "value": "application/json"},
            *item["request"]["header"],
        ]
        item["request"]["body"] = {
            "mode": "raw",
            "raw": raw if raw is not None else json.dumps(body, ensure_ascii=False, indent=2),
            "options": {"raw": {"language": "json"}},
        }

    event = []
    if tests:
        event.append(
            {
                "listen": "test",
                "script": {"type": "text/javascript", "exec": tests.splitlines()},
            }
        )
    if event:
        item["event"] = event
    return item


def folder(name: str, description: str, items: list[dict]) -> dict:
    return {"name": name, "description": description, "item": items}


SAVE_COOKIES = """
if (pm.cookies.has('access_token')) {
  pm.collectionVariables.set('access_token', pm.cookies.get('access_token'));
}
if (pm.cookies.has('refresh_token')) {
  pm.collectionVariables.set('refresh_token', pm.cookies.get('refresh_token'));
}
""".strip()

SAVE_THERAPIST = """
const j = pm.response.json();
if (j.user && j.user.id) {
  pm.collectionVariables.set('therapist_user_id', j.user.id);
}
if (pm.cookies.has('access_token')) {
  pm.collectionVariables.set('therapist_access_token', pm.cookies.get('access_token'));
  pm.collectionVariables.set('access_token', pm.cookies.get('access_token'));
}
if (pm.cookies.has('refresh_token')) {
  pm.collectionVariables.set('refresh_token', pm.cookies.get('refresh_token'));
}
""".strip()

SAVE_PATIENT = """
const j = pm.response.json();
if (j.user && j.user.id) {
  pm.collectionVariables.set('patient_user_id', j.user.id);
}
if (pm.cookies.has('access_token')) {
  pm.collectionVariables.set('patient_access_token', pm.cookies.get('access_token'));
  pm.collectionVariables.set('access_token', pm.cookies.get('access_token'));
}
if (pm.cookies.has('refresh_token')) {
  pm.collectionVariables.set('refresh_token', pm.cookies.get('refresh_token'));
}
""".strip()

EXPECT_STATUS = lambda code: f"""
pm.test('Status {code}', function () {{
  pm.response.to.have.status({code});
}});
""".strip()

EXPECT_ERROR = lambda code: f"""
pm.test('Status {code}', function () {{
  pm.response.to.have.status({code});
}});
pm.test('Error envelope', function () {{
  const j = pm.response.json();
  pm.expect(j).to.have.property('error');
  pm.expect(j.error).to.have.property('code');
  pm.expect(j.error).to.have.property('message');
}});
""".strip()


def build() -> dict:
    auth_folder = folder(
        "00 Setup - Auth & seed",
        "Kolejnosc: rejestracja terapeuty -> login -> zapis therapist_profile_id -> rejestracja pacjenta.",
        [
            req(
                "UC-03 Register therapist (happy)",
                "POST",
                "/auth/register/therapist/",
                auth="none",
                body={
                    "email": "{{therapist_email}}",
                    "password": "{{password}}",
                    "first_name": "Anna",
                    "last_name": "Nowak",
                    "pwzf_number": "{{pwzf_number}}",
                    "pwzf_declaration": True,
                },
                description="UC-03 — tworzy User(THERAPIST) + TherapistProfile. Tokeny w cookies httpOnly.",
                tests=EXPECT_STATUS(201) + "\n" + SAVE_THERAPIST,
            ),
            req(
                "UC-03 Register therapist — missing PWZF declaration (400)",
                "POST",
                "/auth/register/therapist/",
                auth="none",
                body={
                    "email": "therapist-bad@example.com",
                    "password": "{{password}}",
                    "first_name": "Bad",
                    "last_name": "Doc",
                    "pwzf_number": "99999",
                    "pwzf_declaration": False,
                },
                description="E: brak oświadczenia PWZFz.",
                tests=EXPECT_ERROR(400),
            ),
            req(
                "UC-03 Register therapist — duplicate PWZF / email (400/409)",
                "POST",
                "/auth/register/therapist/",
                auth="none",
                body={
                    "email": "{{therapist_email}}",
                    "password": "{{password}}",
                    "first_name": "Anna",
                    "last_name": "Nowak",
                    "pwzf_number": "{{pwzf_number}}",
                    "pwzf_declaration": True,
                },
                description="Powtórna rejestracja tym samym e-mailem / PWZFz.",
                tests="pm.test('Conflict or validation', () => pm.expect([400,409]).to.include(pm.response.code));",
            ),
            req(
                "UC-01 Login therapist (happy)",
                "POST",
                "/auth/login/",
                auth="none",
                body={"email": "{{therapist_email}}", "password": "{{password}}"},
                description="UC-01 — JWT w cookies access_token / refresh_token.",
                tests=EXPECT_STATUS(200) + "\n" + SAVE_THERAPIST,
            ),
            req(
                "GET therapist profile → save therapist_profile_id",
                "GET",
                "/therapist/profile/",
                description="Zapisuje therapist_profile_id potrzebne do rejestracji pacjenta.",
                tests=EXPECT_STATUS(200)
                + """
const j = pm.response.json();
pm.collectionVariables.set('therapist_profile_id', j.id);
""",
            ),
            req(
                "UC-02 Register patient (happy)",
                "POST",
                "/auth/register/patient/",
                auth="none",
                body={
                    "email": "{{patient_email}}",
                    "password": "{{password}}",
                    "first_name": "Jan",
                    "last_name": "Kowalski",
                    "therapist_id": "{{therapist_profile_id}}",
                    "consents": {"terms": True, "medical_data": True},
                },
                description="UC-02 — wymaga therapist_id + zgód terms/medical_data.",
                tests=EXPECT_STATUS(201) + "\n" + SAVE_PATIENT,
            ),
            req(
                "UC-02 Register patient — missing consents (400)",
                "POST",
                "/auth/register/patient/",
                auth="none",
                body={
                    "email": "patient-noconsent@example.com",
                    "password": "{{password}}",
                    "first_name": "Jan",
                    "last_name": "Brak",
                    "therapist_id": "{{therapist_profile_id}}",
                    "consents": {"terms": False, "medical_data": True},
                },
                description="E2: brak wymaganych zgód RODO.",
                tests=EXPECT_ERROR(400),
            ),
            req(
                "UC-02 Register patient — email taken (400)",
                "POST",
                "/auth/register/patient/",
                auth="none",
                body={
                    "email": "{{patient_email}}",
                    "password": "{{password}}",
                    "first_name": "Jan",
                    "last_name": "Kowalski",
                    "therapist_id": "{{therapist_profile_id}}",
                    "consents": {"terms": True, "medical_data": True},
                },
                description="E1: e-mail zajęty.",
                tests="pm.test('Duplicate rejected', () => pm.expect([400,409]).to.include(pm.response.code));",
            ),
            req(
                "UC-01 Login patient (happy)",
                "POST",
                "/auth/login/",
                auth="none",
                body={"email": "{{patient_email}}", "password": "{{password}}"},
                tests=EXPECT_STATUS(200) + "\n" + SAVE_PATIENT,
            ),
            req(
                "UC-01 Login — wrong password (401)",
                "POST",
                "/auth/login/",
                auth="none",
                body={"email": "{{patient_email}}", "password": "WrongPass999!"},
                description="E1: błędne dane → AUTH_001.",
                tests=EXPECT_ERROR(401),
            ),
            req(
                "UC-01 Refresh token (cookie or body)",
                "POST",
                "/auth/refresh/",
                auth="none",
                body={"refresh": "{{refresh_token}}"},
                description="Odświeża cookies. Body.refresh opcjonalne gdy cookie refresh_token jest ustawione.",
                tests=EXPECT_STATUS(200) + "\n" + SAVE_COOKIES,
            ),
            req(
                "UC-04 Password reset request",
                "POST",
                "/auth/password-reset/request/",
                auth="none",
                body={"email": "{{patient_email}}"},
                description="Zawsze 200 (anti-enumeration).",
                tests=EXPECT_STATUS(200),
            ),
            req(
                "UC-04 Password reset confirm — invalid token (400)",
                "POST",
                "/auth/password-reset/confirm/",
                auth="none",
                body={"token": "invalid-token", "new_password": "NewSecurePass123!"},
                description="AUTH_002 — token nieprawidłowy/wygasły.",
                tests=EXPECT_ERROR(400),
            ),
            req(
                "Switch role → therapist token",
                "POST",
                "/auth/login/",
                auth="none",
                body={"email": "{{therapist_email}}", "password": "{{password}}"},
                description="Przywraca sesję terapeuty przed folderami web.",
                tests=EXPECT_STATUS(200) + "\n" + SAVE_THERAPIST,
            ),
        ],
    )

    therapist_dash = folder(
        "UC-10 Therapist dashboard",
        "Pulpit terapeuty — widgety.",
        [
            req(
                "GET dashboard stats",
                "GET",
                "/therapist/dashboard/stats/",
                description="visits_today, patients_total.",
                tests=EXPECT_STATUS(200)
                + """
pm.test('Has widgets', () => {
  const j = pm.response.json();
  pm.expect(j).to.have.property('visits_today');
  pm.expect(j).to.have.property('patients_total');
});
""",
            ),
            req(
                "GET dashboard as patient (403)",
                "GET",
                "/therapist/dashboard/stats/",
                description="Po przełączeniu na token pacjenta — zła rola.",
                tests="""
// Użyj patient_access_token ręcznie lub uruchom po login patient
pm.test('Forbidden or unauthorized for wrong role', () => {
  pm.expect([401,403]).to.include(pm.response.code);
});
""",
                auth="bearer",
            ),
        ],
    )

    patients = folder(
        "UC-12 Patients & episodes",
        "Lista pacjentów, karta, epizody leczenia, notatki.",
        [
            req(
                "List patients",
                "GET",
                "/patients/",
                description="Tylko pacjenci przypisani do zalogowanego terapeuty.",
                tests=EXPECT_STATUS(200)
                + """
const j = pm.response.json();
const list = Array.isArray(j) ? j : (j.results || []);
if (list.length) {
  pm.collectionVariables.set('patient_profile_id', list[0].id);
}
""",
            ),
            req(
                "Patient detail",
                "GET",
                "/patients/{{patient_profile_id}}/",
                tests=EXPECT_STATUS(200),
            ),
            req(
                "Create episode (happy)",
                "POST",
                "/patients/{{patient_profile_id}}/episodes/",
                body={
                    "icd10_code": "M54.5",
                    "status": "IN_PROGRESS",
                    "summary_note": "Ból lędźwiowy — epizod start",
                },
                tests=EXPECT_STATUS(201)
                + """
const j = pm.response.json();
pm.collectionVariables.set('episode_id', j.id);
""",
            ),
            req(
                "List episodes",
                "GET",
                "/patients/{{patient_profile_id}}/episodes/",
                tests=EXPECT_STATUS(200),
            ),
            req(
                "Patch episode status",
                "PATCH",
                "/episodes/{{episode_id}}/",
                body={"status": "IN_PROGRESS", "summary_note": "Aktualizacja po pierwszej wizycie"},
                tests=EXPECT_STATUS(200),
            ),
            req(
                "Add visit note",
                "POST",
                "/episodes/{{episode_id}}/notes/",
                body={"content": "Pacjent zgłasza poprawę mobilności.", "visit": None},
                tests=EXPECT_STATUS(201),
            ),
        ],
    )

    body_map = folder(
        "UC-13 Body map (Diagnostic Mapper)",
        "VAS + charakter bólu na regionach ciała.",
        [
            req(
                "Create body-pain entry",
                "POST",
                "/episodes/{{episode_id}}/body-pain/",
                body={
                    "body_region": "LUMBAR",
                    "view_side": "BACK",
                    "vas_score": 7,
                    "pain_character": ["SHARP", "RADIATING"],
                },
                tests=EXPECT_STATUS(201)
                + """
pm.collectionVariables.set('body_pain_id', pm.response.json().id);
""",
            ),
            req(
                "List body-pain",
                "GET",
                "/episodes/{{episode_id}}/body-pain/",
                tests=EXPECT_STATUS(200),
            ),
            req(
                "Update body-pain (PUT)",
                "PUT",
                "/episodes/{{episode_id}}/body-pain/{{body_pain_id}}/",
                body={
                    "body_region": "LUMBAR",
                    "view_side": "BACK",
                    "vas_score": 4,
                    "pain_character": ["DULL"],
                },
                tests=EXPECT_STATUS(200),
            ),
            req(
                "Create body-pain — VAS out of range (400)",
                "POST",
                "/episodes/{{episode_id}}/body-pain/",
                body={
                    "body_region": "THIGH_RIGHT",
                    "view_side": "FRONT",
                    "vas_score": 15,
                    "pain_character": ["SHARP"],
                },
                tests=EXPECT_ERROR(400),
            ),
        ],
    )

    scheduling = folder(
        "UC-07 / UC-11 / UC-14 Visits & schedule",
        "Harmonogram terapeuty + wizyty pacjenta (reschedule/cancel).",
        [
            req(
                "Create therapy type",
                "POST",
                "/therapist/therapy-types/",
                body={"name": "Terapia manualna", "color_hex": "#3B82F6", "duration_min": 45},
                tests=EXPECT_STATUS(201)
                + """
pm.collectionVariables.set('therapy_type_id', pm.response.json().id);
""",
            ),
            req(
                "List therapy types",
                "GET",
                "/therapist/therapy-types/",
                tests=EXPECT_STATUS(200),
            ),
            req(
                "Create visit (happy)",
                "POST",
                "/therapist/visits/",
                body={
                    "patient_id": "{{patient_profile_id}}",
                    "episode_id": "{{episode_id}}",
                    "therapy_type_id": "{{therapy_type_id}}",
                    "start_at": "{{visit_start}}",
                    "end_at": "{{visit_end}}",
                    "location_address": "ul. Przykładowa 1, Tarnów",
                    "prep_instructions": "Proszę zabrać aktualne wyniki badań.",
                },
                tests=EXPECT_STATUS(201)
                + """
pm.collectionVariables.set('visit_id', pm.response.json().id);
""",
            ),
            req(
                "Create visit — overlap (400)",
                "POST",
                "/therapist/visits/",
                body={
                    "patient_id": "{{patient_profile_id}}",
                    "episode_id": "{{episode_id}}",
                    "therapy_type_id": "{{therapy_type_id}}",
                    "start_at": "{{visit_start}}",
                    "end_at": "{{visit_end}}",
                    "location_address": "ul. Przykładowa 1, Tarnów",
                },
                description="E1: kolizja terminów (ExclusionConstraint).",
                tests=EXPECT_ERROR(400),
            ),
            req(
                "Therapist day schedule",
                "GET",
                "/therapist/visits/",
                query=[("date", "{{schedule_date}}")],
                tests=EXPECT_STATUS(200),
            ),
            req(
                "Patch visit (drag slot)",
                "PATCH",
                "/therapist/visits/{{visit_id}}/",
                body={
                    "start_at": "{{visit_start_alt}}",
                    "end_at": "{{visit_end_alt}}",
                },
                tests=EXPECT_STATUS(200),
            ),
            req(
                "Visit detail",
                "GET",
                "/visits/{{visit_id}}/",
                tests=EXPECT_STATUS(200),
            ),
            req(
                "Login as patient (for me/visits)",
                "POST",
                "/auth/login/",
                auth="none",
                body={"email": "{{patient_email}}", "password": "{{password}}"},
                tests=EXPECT_STATUS(200) + "\n" + SAVE_PATIENT,
            ),
            req(
                "Patient upcoming visits",
                "GET",
                "/me/visits/",
                query=[("status", "upcoming")],
                tests=EXPECT_STATUS(200),
            ),
            req(
                "Patient past visits",
                "GET",
                "/me/visits/",
                query=[("status", "past")],
                tests=EXPECT_STATUS(200),
            ),
            req(
                "Patient reschedule visit",
                "PATCH",
                "/visits/{{visit_id}}/reschedule/",
                body={
                    "start_at": "{{visit_start_patient}}",
                    "end_at": "{{visit_end_patient}}",
                },
                tests=EXPECT_STATUS(200),
            ),
            req(
                "Cancel visit",
                "POST",
                "/visits/{{visit_id}}/cancel/",
                body={"cancel_reason": "Konflikt godzinowy pacjenta"},
                tests=EXPECT_STATUS(200),
            ),
            req(
                "Re-login therapist",
                "POST",
                "/auth/login/",
                auth="none",
                body={"email": "{{therapist_email}}", "password": "{{password}}"},
                tests=EXPECT_STATUS(200) + "\n" + SAVE_THERAPIST,
            ),
        ],
    )

    exercises = folder(
        "UC-06 / UC-15 Exercises & compliance",
        "Katalog ćwiczeń, przypisanie, oznaczenie wykonania.",
        [
            req(
                "Create exercise (multipart)",
                "POST",
                "/therapist/exercises/",
                formdata=[
                    {"key": "title", "value": "Mostek biodrowy", "type": "text"},
                    {"key": "media_type", "value": "VIDEO", "type": "text"},
                    {"key": "instruction", "value": "3 serie × 10 powtórzeń", "type": "text"},
                    {
                        "key": "file",
                        "type": "file",
                        "src": "",
                        "description": "Wybierz lokalny plik .mp4 lub .pdf w Postmanie",
                    },
                ],
                description="Wymaga pliku (mp4/pdf). Ustaw src w UI Postmana.",
                tests="""
pm.test('Created or file required', () => {
  pm.expect([201,400]).to.include(pm.response.code);
  if (pm.response.code === 201) {
    pm.collectionVariables.set('exercise_id', pm.response.json().id);
  }
});
""",
            ),
            req(
                "List exercises",
                "GET",
                "/therapist/exercises/",
                tests=EXPECT_STATUS(200)
                + """
const j = pm.response.json();
const list = Array.isArray(j) ? j : (j.results || []);
if (list.length && !pm.collectionVariables.get('exercise_id')) {
  pm.collectionVariables.set('exercise_id', list[0].id);
}
""",
            ),
            req(
                "Assign exercise to patient",
                "POST",
                "/therapist/exercise-assignments/",
                body={
                    "exercise_id": "{{exercise_id}}",
                    "patient_id": "{{patient_profile_id}}",
                    "episode_id": "{{episode_id}}",
                    "dosage": "3 serie x 10 powt.",
                    "start_date": "{{assignment_start}}",
                    "end_date": "{{assignment_end}}",
                },
                tests=EXPECT_STATUS(201)
                + """
pm.collectionVariables.set('assignment_id', pm.response.json().id);
""",
            ),
            req(
                "Login patient",
                "POST",
                "/auth/login/",
                auth="none",
                body={"email": "{{patient_email}}", "password": "{{password}}"},
                tests=EXPECT_STATUS(200) + "\n" + SAVE_PATIENT,
            ),
            req(
                "UC-05/06 Exercises today",
                "GET",
                "/me/exercises/today/",
                tests=EXPECT_STATUS(200),
            ),
            req(
                "Mark exercise completion",
                "POST",
                "/me/exercise-completions/",
                body={
                    "assignment_id": "{{assignment_id}}",
                    "completed_on": "{{today}}",
                    "done": True,
                },
                tests=EXPECT_STATUS(201),
            ),
            req(
                "Completion — foreign assignment (400)",
                "POST",
                "/me/exercise-completions/",
                body={
                    "assignment_id": "00000000-0000-0000-0000-000000000099",
                    "completed_on": "{{today}}",
                    "done": True,
                },
                tests=EXPECT_ERROR(400),
            ),
            req(
                "Re-login therapist",
                "POST",
                "/auth/login/",
                auth="none",
                body={"email": "{{therapist_email}}", "password": "{{password}}"},
                tests=EXPECT_STATUS(200) + "\n" + SAVE_THERAPIST,
            ),
        ],
    )

    documents = folder(
        "UC-08 Documents",
        "Upload PDF przez terapeutę, lista i download przez pacjenta.",
        [
            req(
                "Therapist upload document",
                "POST",
                "/therapist/documents/",
                formdata=[
                    {"key": "patient_id", "value": "{{patient_profile_id}}", "type": "text"},
                    {"key": "title", "value": "Wyniki RTG", "type": "text"},
                    {"key": "episode_id", "value": "{{episode_id}}", "type": "text"},
                    {
                        "key": "file",
                        "type": "file",
                        "src": "",
                        "description": "PDF medyczny",
                    },
                ],
                tests="""
pm.test('Created or file required', () => {
  pm.expect([201,400,404]).to.include(pm.response.code);
  if (pm.response.code === 201) {
    pm.collectionVariables.set('document_id', pm.response.json().id);
  }
});
""",
            ),
            req(
                "Login patient",
                "POST",
                "/auth/login/",
                auth="none",
                body={"email": "{{patient_email}}", "password": "{{password}}"},
                tests=EXPECT_STATUS(200) + "\n" + SAVE_PATIENT,
            ),
            req(
                "List my documents",
                "GET",
                "/me/documents/",
                tests=EXPECT_STATUS(200)
                + """
const j = pm.response.json();
const list = Array.isArray(j) ? j : (j.results || []);
if (list.length) pm.collectionVariables.set('document_id', list[0].id);
""",
            ),
            req(
                "Download document",
                "GET",
                "/{{document_id}}/download/",
                description="Ścieżka zgodna z backendem: GET /api/v1/{id}/download/",
                tests="pm.test('OK or 404', () => pm.expect([200,404]).to.include(pm.response.code));",
            ),
            req(
                "Re-login therapist",
                "POST",
                "/auth/login/",
                auth="none",
                body={"email": "{{therapist_email}}", "password": "{{password}}"},
                tests=EXPECT_STATUS(200) + "\n" + SAVE_THERAPIST,
            ),
        ],
    )

    therapist_profile = folder(
        "UC-16 / UC-17 Therapist profile",
        "Profil własny + wizytówka publiczna.",
        [
            req(
                "GET own profile",
                "GET",
                "/therapist/profile/",
                tests=EXPECT_STATUS(200),
            ),
            req(
                "PATCH profile (bio, courses)",
                "PATCH",
                "/therapist/profile/",
                body={
                    "phone": "+48123123123",
                    "bio": "Specjalista terapii manualnej i sportowej.",
                    "courses": ["PNF", "Terapia tkanek miękkich"],
                },
                tests=EXPECT_STATUS(200),
            ),
            req(
                "Login patient → public profile",
                "POST",
                "/auth/login/",
                auth="none",
                body={"email": "{{patient_email}}", "password": "{{password}}"},
                tests=EXPECT_STATUS(200) + "\n" + SAVE_PATIENT,
            ),
            req(
                "GET public therapist profile",
                "GET",
                "/therapists/{{therapist_profile_id}}/public/",
                tests=EXPECT_STATUS(200),
            ),
        ],
    )

    patient_me = folder(
        "UC-05 / UC-09 / UC-18 Patient me & privacy",
        "Profil, zgody, eksport, usunięcie, preferencje powiadomień.",
        [
            req(
                "GET me/profile",
                "GET",
                "/me/profile/",
                tests=EXPECT_STATUS(200),
            ),
            req(
                "PATCH me/profile",
                "PATCH",
                "/me/profile/",
                body={"phone": "+48987654321", "pesel": "90010112345"},
                tests=EXPECT_STATUS(200),
            ),
            req(
                "GET consents",
                "GET",
                "/me/consents/",
                tests=EXPECT_STATUS(200),
            ),
            req(
                "PATCH optional consents",
                "PATCH",
                "/me/consents/optional/",
                body={"marketing": False, "research": True},
                tests=EXPECT_STATUS(200),
            ),
            req(
                "POST data-export (RODO)",
                "POST",
                "/me/data-export/",
                tests=EXPECT_STATUS(200),
            ),
            req(
                "POST account-deletion-request",
                "POST",
                "/me/account-deletion-request/",
                tests=EXPECT_STATUS(202),
            ),
            req(
                "GET notification preferences",
                "GET",
                "/me/notification-preferences/",
                tests=EXPECT_STATUS(200),
            ),
            req(
                "PATCH notification preferences",
                "PATCH",
                "/me/notification-preferences/",
                body={
                    "visit_reminders": True,
                    "visit_changes": True,
                    "waitlist": False,
                    "exercise_reminders": True,
                    "new_documents": True,
                },
                tests=EXPECT_STATUS(200),
            ),
            req(
                "Unauthenticated me/profile (401)",
                "GET",
                "/me/profile/",
                auth="none",
                tests=EXPECT_ERROR(401),
            ),
        ],
    )

    security = folder(
        "Security & role guards",
        "Przypadki cross-role i brak tokena.",
        [
            req(
                "Patient cannot list therapist patients",
                "GET",
                "/patients/",
                description="Uruchom z patient_access_token (Bearer).",
                tests="pm.test('403/401', () => pm.expect([401,403]).to.include(pm.response.code));",
            ),
            req(
                "No token → 401 on protected",
                "GET",
                "/therapist/profile/",
                auth="none",
                tests=EXPECT_ERROR(401),
            ),
        ],
    )

    collection = {
        "info": {
            "name": "PhysioCare API",
            "description": (
                "Pełna kolekcja kontraktu REST PhysioCare (`/api/v1`).\n\n"
                "Pokrywa UC-01–UC-18: happy path + wyjątki (400/401/403/409).\n\n"
                "**Auth:** JWT w cookies `access_token` / `refresh_token` (httpOnly). "
                "Kolekcja dodatkowo ustawia `{{access_token}}` z jar cookies (gdy dostępne) "
                "i wysyła `Authorization: Bearer`.\n\n"
                "**Kolejność Collection Runner:** folder `00 Setup`, potem pozostałe foldery.\n\n"
                "Dokumentacja: `docs/postman-testing.md`, kontrakt: `docs/api.md`."
            ),
            "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
        },
        "auth": {
            "type": "bearer",
            "bearer": [{"key": "token", "value": "{{access_token}}", "type": "string"}],
        },
        "variable": [
            {"key": "baseUrl", "value": "http://localhost:8000/api/v1"},
            {"key": "access_token", "value": ""},
            {"key": "refresh_token", "value": ""},
            {"key": "therapist_access_token", "value": ""},
            {"key": "patient_access_token", "value": ""},
            {"key": "therapist_email", "value": "terapeuta@example.com"},
            {"key": "patient_email", "value": "pacjent@example.com"},
            {"key": "password", "value": "SecurePass123!"},
            {"key": "pwzf_number", "value": "71239"},
            {"key": "therapist_profile_id", "value": ""},
            {"key": "patient_profile_id", "value": ""},
            {"key": "episode_id", "value": ""},
            {"key": "body_pain_id", "value": ""},
            {"key": "therapy_type_id", "value": ""},
            {"key": "visit_id", "value": ""},
            {"key": "exercise_id", "value": ""},
            {"key": "assignment_id", "value": ""},
            {"key": "document_id", "value": ""},
            {"key": "schedule_date", "value": "2026-08-10"},
            {"key": "visit_start", "value": "2026-08-10T11:00:00+02:00"},
            {"key": "visit_end", "value": "2026-08-10T11:45:00+02:00"},
            {"key": "visit_start_alt", "value": "2026-08-10T14:00:00+02:00"},
            {"key": "visit_end_alt", "value": "2026-08-10T14:45:00+02:00"},
            {"key": "visit_start_patient", "value": "2026-08-11T10:00:00+02:00"},
            {"key": "visit_end_patient", "value": "2026-08-11T10:45:00+02:00"},
            {"key": "assignment_start", "value": "2026-08-03"},
            {"key": "assignment_end", "value": "2026-08-17"},
            {"key": "today", "value": "2026-08-03"},
        ],
        "item": [
            auth_folder,
            therapist_dash,
            patients,
            body_map,
            scheduling,
            exercises,
            documents,
            therapist_profile,
            patient_me,
            security,
        ],
    }
    return collection


def build_env() -> dict:
    return {
        "id": "physiocare-local",
        "name": "PhysioCare Local",
        "values": [
            {"key": "baseUrl", "value": "http://localhost:8000/api/v1", "enabled": True},
            {"key": "therapist_email", "value": "terapeuta@example.com", "enabled": True},
            {"key": "patient_email", "value": "pacjent@example.com", "enabled": True},
            {"key": "password", "value": "SecurePass123!", "type": "secret", "enabled": True},
            {"key": "pwzf_number", "value": "71239", "enabled": True},
            {"key": "access_token", "value": "", "type": "secret", "enabled": True},
            {"key": "refresh_token", "value": "", "type": "secret", "enabled": True},
        ],
        "_postman_variable_scope": "environment",
    }


def main() -> None:
    collection = build()
    env = build_env()
    OUT_COLLECTION.parent.mkdir(parents=True, exist_ok=True)
    OUT_COLLECTION.write_text(
        json.dumps(collection, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    OUT_ENV.write_text(json.dumps(env, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    OUT_COPY.parent.mkdir(parents=True, exist_ok=True)
    OUT_COPY.write_text(OUT_COLLECTION.read_text(encoding="utf-8"), encoding="utf-8")
    print(f"Wrote {OUT_COLLECTION}")
    print(f"Wrote {OUT_ENV}")
    print(f"Copied {OUT_COPY}")


if __name__ == "__main__":
    main()
