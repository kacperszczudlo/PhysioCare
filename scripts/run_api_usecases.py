#!/usr/bin/env python3
"""Run PhysioCare API use-case smoke flow against local runserver."""
from __future__ import annotations

import json
import sys
import uuid
from datetime import date, datetime, timedelta, timezone
from http.cookiejar import CookieJar
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import HTTPCookieProcessor, Request, build_opener

BASE = "http://127.0.0.1:8000/api/v1"
ROOT = Path(__file__).resolve().parents[1]
MEDIA_SAMPLE = ROOT / "backend" / "media" / "_postman_sample.pdf"

results: list[tuple[str, int, int | None, str]] = []
state: dict = {}
opener = build_opener(HTTPCookieProcessor(CookieJar()))


def log(name: str, expected: int | set[int], got: int | None, detail: str = "") -> None:
    exp = expected if isinstance(expected, set) else {expected}
    ok = got in exp
    mark = "PASS" if ok else "FAIL"
    exp_s = "|".join(str(x) for x in sorted(exp))
    results.append((name, next(iter(exp)) if len(exp) == 1 else -1, got, mark))
    print(f"[{mark}] {name}  expected={exp_s} got={got} {detail}".rstrip())


def call(
    name: str,
    method: str,
    path: str,
    *,
    expected: int | set[int],
    body: dict | None = None,
    form: dict | None = None,
    files: dict | None = None,
) -> dict | bytes | None:
    url = BASE + path
    data = None
    headers = {"Accept": "application/json"}

    if files is not None:
        boundary = f"----Physio{uuid.uuid4().hex}"
        headers["Content-Type"] = f"multipart/form-data; boundary={boundary}"
        parts: list[bytes] = []
        fields = form or {}
        for k, v in fields.items():
            parts.append(
                f"--{boundary}\r\nContent-Disposition: form-data; name=\"{k}\"\r\n\r\n{v}\r\n".encode()
            )
        for k, (filename, content, ctype) in files.items():
            parts.append(
                (
                    f"--{boundary}\r\n"
                    f'Content-Disposition: form-data; name="{k}"; filename="{filename}"\r\n'
                    f"Content-Type: {ctype}\r\n\r\n"
                ).encode()
                + content
                + b"\r\n"
            )
        parts.append(f"--{boundary}--\r\n".encode())
        data = b"".join(parts)
    elif body is not None:
        data = json.dumps(body).encode()
        headers["Content-Type"] = "application/json"

    req = Request(url, data=data, headers=headers, method=method)
    try:
        with opener.open(req, timeout=30) as resp:
            raw = resp.read()
            got = resp.status
            log(name, expected, got)
            if not raw:
                return None
            ctype = resp.headers.get("Content-Type", "")
            if "application/json" in ctype:
                return json.loads(raw.decode())
            return raw
    except HTTPError as e:
        raw = e.read()
        got = e.code
        detail = ""
        try:
            j = json.loads(raw.decode())
            detail = json.dumps(j, ensure_ascii=False)[:200]
            log(name, expected, got, detail)
            return j
        except Exception:
            log(name, expected, got, raw[:120].decode(errors="replace"))
            return None
    except URLError as e:
        log(name, expected, None, str(e))
        return None


def main() -> int:
    stamp = uuid.uuid4().hex[:8]
    therapist_email = f"therapist_{stamp}@example.com"
    patient_email = f"patient_{stamp}@example.com"
    password = "SecurePass123!"
    pwzf = f"7{stamp[:4]}"

    today = date.today()
    start = datetime.now(timezone(timedelta(hours=2))).replace(microsecond=0) + timedelta(days=2, hours=2)
    end = start + timedelta(minutes=45)
    start_alt = start + timedelta(hours=3)
    end_alt = start_alt + timedelta(minutes=45)
    start_p = start + timedelta(days=1)
    end_p = start_p + timedelta(minutes=45)

    # --- UC-03 / UC-01 / UC-02 / UC-04 ---
    r = call(
        "UC-03 Register therapist",
        "POST",
        "/auth/register/therapist/",
        expected=201,
        body={
            "email": therapist_email,
            "password": password,
            "first_name": "Anna",
            "last_name": "Nowak",
            "pwzf_number": pwzf,
            "pwzf_declaration": True,
        },
    )
    call(
        "UC-03 missing PWZF declaration",
        "POST",
        "/auth/register/therapist/",
        expected=400,
        body={
            "email": f"bad_{stamp}@example.com",
            "password": password,
            "first_name": "Bad",
            "last_name": "Doc",
            "pwzf_number": "99999",
            "pwzf_declaration": False,
        },
    )
    call(
        "UC-03 duplicate therapist",
        "POST",
        "/auth/register/therapist/",
        expected={400, 409},
        body={
            "email": therapist_email,
            "password": password,
            "first_name": "Anna",
            "last_name": "Nowak",
            "pwzf_number": pwzf,
            "pwzf_declaration": True,
        },
    )
    call(
        "UC-01 Login therapist",
        "POST",
        "/auth/login/",
        expected=200,
        body={"email": therapist_email, "password": password},
    )
    r = call("GET therapist profile", "GET", "/therapist/profile/", expected=200)
    if isinstance(r, dict):
        state["therapist_profile_id"] = r["id"]

    call(
        "UC-02 Register patient",
        "POST",
        "/auth/register/patient/",
        expected=201,
        body={
            "email": patient_email,
            "password": password,
            "first_name": "Jan",
            "last_name": "Kowalski",
            "therapist_id": state.get("therapist_profile_id"),
            "consents": {"terms": True, "medical_data": True},
        },
    )
    call(
        "UC-02 missing consents",
        "POST",
        "/auth/register/patient/",
        expected=400,
        body={
            "email": f"noconsent_{stamp}@example.com",
            "password": password,
            "first_name": "Jan",
            "last_name": "Brak",
            "therapist_id": state.get("therapist_profile_id"),
            "consents": {"terms": False, "medical_data": True},
        },
    )
    call(
        "UC-02 email taken",
        "POST",
        "/auth/register/patient/",
        expected={400, 409},
        body={
            "email": patient_email,
            "password": password,
            "first_name": "Jan",
            "last_name": "Kowalski",
            "therapist_id": state.get("therapist_profile_id"),
            "consents": {"terms": True, "medical_data": True},
        },
    )
    call(
        "UC-01 Login patient",
        "POST",
        "/auth/login/",
        expected=200,
        body={"email": patient_email, "password": password},
    )
    call(
        "UC-01 wrong password",
        "POST",
        "/auth/login/",
        expected=401,
        body={"email": patient_email, "password": "WrongPass999!"},
    )
    call("UC-01 Refresh", "POST", "/auth/refresh/", expected=200, body={})
    call(
        "UC-04 reset request",
        "POST",
        "/auth/password-reset/request/",
        expected=200,
        body={"email": patient_email},
    )
    call(
        "UC-04 reset invalid token",
        "POST",
        "/auth/password-reset/confirm/",
        expected=400,
        body={"token": "invalid-token", "new_password": "NewSecurePass123!"},
    )
    call(
        "Switch to therapist",
        "POST",
        "/auth/login/",
        expected=200,
        body={"email": therapist_email, "password": password},
    )

    # --- UC-10 ---
    call("UC-10 dashboard stats", "GET", "/therapist/dashboard/stats/", expected=200)

    # --- UC-12 ---
    r = call("UC-12 list patients", "GET", "/patients/", expected=200)
    if isinstance(r, list) and r:
        state["patient_profile_id"] = r[0]["id"]
    elif isinstance(r, dict) and r.get("results"):
        state["patient_profile_id"] = r["results"][0]["id"]

    call(
        "UC-12 patient detail",
        "GET",
        f"/patients/{state.get('patient_profile_id')}/",
        expected=200,
    )
    r = call(
        "UC-12 create episode",
        "POST",
        f"/patients/{state.get('patient_profile_id')}/episodes/",
        expected=201,
        body={"icd10_code": "M54.5", "status": "IN_PROGRESS", "summary_note": "Ból lędźwiowy"},
    )
    if isinstance(r, dict) and r.get("id"):
        state["episode_id"] = r["id"]
    r = call(
        "UC-12 list episodes",
        "GET",
        f"/patients/{state.get('patient_profile_id')}/episodes/",
        expected=200,
    )
    if not state.get("episode_id"):
        episodes = r if isinstance(r, list) else (r or {}).get("results", [])
        if episodes:
            state["episode_id"] = episodes[0]["id"]
    call(
        "UC-12 patch episode",
        "PATCH",
        f"/episodes/{state.get('episode_id')}/",
        expected=200,
        body={"summary_note": "Aktualizacja"},
    )
    call(
        "UC-12 visit note",
        "POST",
        f"/episodes/{state.get('episode_id')}/notes/",
        expected=201,
        body={"content": "Poprawa mobilności"},
    )

    # --- UC-13 ---
    r = call(
        "UC-13 body-pain create",
        "POST",
        f"/episodes/{state.get('episode_id')}/body-pain/",
        expected=201,
        body={
            "body_region": "LUMBAR",
            "view_side": "BACK",
            "vas_score": 7,
            "pain_character": ["SHARP", "RADIATING"],
        },
    )
    if isinstance(r, dict):
        state["body_pain_id"] = r["id"]
    call(
        "UC-13 body-pain list",
        "GET",
        f"/episodes/{state.get('episode_id')}/body-pain/",
        expected=200,
    )
    call(
        "UC-13 body-pain update",
        "PUT",
        f"/episodes/{state.get('episode_id')}/body-pain/{state.get('body_pain_id')}/",
        expected=200,
        body={
            "body_region": "LUMBAR",
            "view_side": "BACK",
            "vas_score": 4,
            "pain_character": ["DULL"],
        },
    )
    call(
        "UC-13 VAS out of range",
        "POST",
        f"/episodes/{state.get('episode_id')}/body-pain/",
        expected=400,
        body={
            "body_region": "THIGH_RIGHT",
            "view_side": "FRONT",
            "vas_score": 15,
            "pain_character": ["SHARP"],
        },
    )

    # --- UC-11 / 07 / 14 ---
    r = call(
        "UC-11 create therapy type",
        "POST",
        "/therapist/therapy-types/",
        expected=201,
        body={"name": f"Manualna {stamp}", "color_hex": "#3B82F6", "duration_min": 45},
    )
    if isinstance(r, dict):
        state["therapy_type_id"] = r["id"]
    r = call(
        "UC-11 create visit",
        "POST",
        "/therapist/visits/",
        expected=201,
        body={
            "patient_id": state.get("patient_profile_id"),
            "episode_id": state.get("episode_id"),
            "therapy_type_id": state.get("therapy_type_id"),
            "start_at": start.isoformat(),
            "end_at": end.isoformat(),
            "location_address": "ul. Testowa 1",
            "prep_instructions": "Wyniki badań",
        },
    )
    if isinstance(r, dict):
        state["visit_id"] = r["id"]
    call(
        "UC-11 visit overlap",
        "POST",
        "/therapist/visits/",
        expected=400,
        body={
            "patient_id": state.get("patient_profile_id"),
            "episode_id": state.get("episode_id"),
            "therapy_type_id": state.get("therapy_type_id"),
            "start_at": start.isoformat(),
            "end_at": end.isoformat(),
        },
    )
    call(
        "UC-11 day schedule",
        "GET",
        f"/therapist/visits/?date={start.date().isoformat()}",
        expected=200,
    )
    call(
        "UC-14 patch visit",
        "PATCH",
        f"/therapist/visits/{state.get('visit_id')}/",
        expected=200,
        body={"start_at": start_alt.isoformat(), "end_at": end_alt.isoformat()},
    )
    call("UC-07 visit detail", "GET", f"/visits/{state.get('visit_id')}/", expected=200)

    call(
        "Login patient (visits)",
        "POST",
        "/auth/login/",
        expected=200,
        body={"email": patient_email, "password": password},
    )
    call("UC-07 me visits upcoming", "GET", "/me/visits/?status=upcoming", expected=200)
    call("UC-07 me visits past", "GET", "/me/visits/?status=past", expected=200)
    call(
        "UC-07 reschedule",
        "PATCH",
        f"/visits/{state.get('visit_id')}/reschedule/",
        expected=200,
        body={"start_at": start_p.isoformat(), "end_at": end_p.isoformat()},
    )
    call(
        "UC-07/14 cancel visit",
        "POST",
        f"/visits/{state.get('visit_id')}/cancel/",
        expected=200,
        body={"cancel_reason": "Konflikt"},
    )

    call(
        "Re-login therapist",
        "POST",
        "/auth/login/",
        expected=200,
        body={"email": therapist_email, "password": password},
    )

    # --- UC-15 / 06 ---
    MEDIA_SAMPLE.parent.mkdir(parents=True, exist_ok=True)
    if not MEDIA_SAMPLE.exists():
        MEDIA_SAMPLE.write_bytes(
            b"%PDF-1.1\n1 0 obj<<>>endobj\ntrailer<<>>\n%%EOF\n"
        )
    pdf = MEDIA_SAMPLE.read_bytes()
    r = call(
        "UC-15 create exercise",
        "POST",
        "/therapist/exercises/",
        expected=201,
        form={
            "title": f"Mostek {stamp}",
            "media_type": "PDF",
            "instruction": "3x10",
        },
        files={"file": ("sample.pdf", pdf, "application/pdf")},
    )
    if isinstance(r, dict):
        state["exercise_id"] = r["id"]
    r = call(
        "UC-15 assign exercise",
        "POST",
        "/therapist/exercise-assignments/",
        expected=201,
        body={
            "exercise_id": state.get("exercise_id"),
            "patient_id": state.get("patient_profile_id"),
            "episode_id": state.get("episode_id"),
            "dosage": "3x10",
            "start_date": today.isoformat(),
            "end_date": (today + timedelta(days=14)).isoformat(),
        },
    )
    if isinstance(r, dict):
        state["assignment_id"] = r["id"]

    call(
        "Login patient (exercises)",
        "POST",
        "/auth/login/",
        expected=200,
        body={"email": patient_email, "password": password},
    )
    call("UC-05/06 exercises today", "GET", "/me/exercises/today/", expected=200)
    call(
        "UC-06 completion",
        "POST",
        "/me/exercise-completions/",
        expected=201,
        body={
            "assignment_id": state.get("assignment_id"),
            "completed_on": today.isoformat(),
            "done": True,
        },
    )
    call(
        "UC-06 foreign assignment",
        "POST",
        "/me/exercise-completions/",
        expected=400,
        body={
            "assignment_id": "00000000-0000-0000-0000-000000000099",
            "completed_on": today.isoformat(),
            "done": True,
        },
    )

    call(
        "Re-login therapist (docs)",
        "POST",
        "/auth/login/",
        expected=200,
        body={"email": therapist_email, "password": password},
    )

    # --- UC-08 ---
    r = call(
        "UC-08 upload document",
        "POST",
        "/therapist/documents/",
        expected=201,
        form={
            "patient_id": state.get("patient_profile_id"),
            "title": "Wyniki RTG",
            "episode_id": state.get("episode_id"),
        },
        files={"file": ("rtg.pdf", pdf, "application/pdf")},
    )
    if isinstance(r, dict):
        state["document_id"] = r["id"]

    call(
        "Login patient (docs)",
        "POST",
        "/auth/login/",
        expected=200,
        body={"email": patient_email, "password": password},
    )
    call("UC-08 list documents", "GET", "/me/documents/", expected=200)
    call(
        "UC-08 download",
        "GET",
        f"/{state.get('document_id')}/download/",
        expected=200,
    )

    # --- UC-16 / 17 ---
    call(
        "Re-login therapist (profile)",
        "POST",
        "/auth/login/",
        expected=200,
        body={"email": therapist_email, "password": password},
    )
    call("UC-16 get profile", "GET", "/therapist/profile/", expected=200)
    call(
        "UC-16 patch profile",
        "PATCH",
        "/therapist/profile/",
        expected=200,
        body={
            "phone": "+48123123123",
            "bio": "Terapia manualna",
            "courses": ["PNF"],
        },
    )
    call(
        "Login patient (public)",
        "POST",
        "/auth/login/",
        expected=200,
        body={"email": patient_email, "password": password},
    )
    call(
        "UC-17 public therapist",
        "GET",
        f"/therapists/{state.get('therapist_profile_id')}/public/",
        expected=200,
    )

    # --- UC-09 / 18 ---
    call("UC-09 me profile", "GET", "/me/profile/", expected=200)
    call(
        "UC-09 patch profile",
        "PATCH",
        "/me/profile/",
        expected=200,
        body={"phone": "+48987654321"},
    )
    call("UC-09 consents", "GET", "/me/consents/", expected=200)
    call(
        "UC-09 optional consents",
        "PATCH",
        "/me/consents/optional/",
        expected=200,
        body={"marketing": False, "research": True},
    )
    call("UC-09 data export", "POST", "/me/data-export/", expected=200)
    call("UC-09 deletion request", "POST", "/me/account-deletion-request/", expected=202)
    call("UC-18 get notif prefs", "GET", "/me/notification-preferences/", expected=200)
    call(
        "UC-18 patch notif prefs",
        "PATCH",
        "/me/notification-preferences/",
        expected=200,
        body={"visit_reminders": True, "exercise_reminders": True},
    )

    # --- Security: unauthenticated (new opener without cookies) ---
    global opener
    opener = build_opener(HTTPCookieProcessor(CookieJar()))
    call("Security no token profile", "GET", "/me/profile/", expected=401)
    call("Security no token therapist", "GET", "/therapist/profile/", expected=401)

    passed = sum(1 for *_, m in results if m == "PASS")
    failed = sum(1 for *_, m in results if m == "FAIL")
    print()
    print(f"TOTAL {len(results)}  PASS {passed}  FAIL {failed}")
    if failed:
        print("\nFailed:")
        for name, exp, got, mark in results:
            if mark == "FAIL":
                print(f"  - {name}: got {got}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
