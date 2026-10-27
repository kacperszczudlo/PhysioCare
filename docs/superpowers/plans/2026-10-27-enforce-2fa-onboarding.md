# Enforce 2FA Onboarding for Therapists and Admins Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Enforce mandatory two-factor authentication (2FA/TOTP) setup for therapists and administrators upon registering or accessing the web app without active MFA, preventing account lockouts on subsequent logins and ensuring RODO/medical data compliance.

**Architecture:** Extend backend `_user_payload` to include `has_mfa` and `mfa_required` flags. Create a dedicated non-closable `MFAEnforcementModal` embedded into `AppLayout` and `AdminLayout` that guides medical staff through QR code scanning, TOTP verification, and backup codes generation before granting full access to medical panels.

**Tech Stack:** Django REST Framework, pyotp, React 19, TypeScript, Vite, React Router v6, Vitest, pytest-django.

**Spec:** Wariant 1 (Blokujący Onboarding 2FA) agreed with the user.

## Global Constraints

- No external dependencies to add (DRF, pyotp, React, QRCode rendering already supported in codebase).
- Must adhere to Conventional Commits and 50/72 rule for all commit drafts.
- Do not bypass existing 2FA flows on mobile or patient routes (patients do not have mandatory 2FA).
- All changes must be fully tested (pytest for backend, vitest for web).
- Update all relevant markdown documentation (`docs/features.md`, `docs/test-cases.md`, `docs/api.md`).

## Review Focus

1. **User with 2FA already active:** Modal must not render or block the user.
2. **Patient user:** Patients must never be forced to configure 2FA on web.
3. **Invalid TOTP entered:** Clear error message without losing the secret or QR code.
4. **Backup codes generation:** Users must receive backup codes and have a one-click copy option before the modal closes.
5. **Session update:** Once activated, `user.has_mfa` in `AuthContext` must update to `true` dynamically without requiring a hard page refresh.

---

### Task 1: Backend `_user_payload` Extension (`has_mfa` & `mfa_required`)

**Files:**
- Modify: `backend/physiocare/accounts/views.py:148-176`
- Test: `backend/tests/accounts/test_current_user.py`

- [ ] **Step 1:** Write failing unit test in `backend/tests/accounts/test_current_user.py` verifying that `GET /api/v1/auth/me/` returns `has_mfa: bool` and `mfa_required: bool`.
- [ ] **Step 2:** Run pytest to verify test failure:
  `cd backend; $env:PYTHONPATH="physiocare;venv/Lib/site-packages"; python -m pytest tests/accounts/test_current_user.py -k test_current_user`
- [ ] **Step 3:** In `backend/physiocare/accounts/views.py`, update `_user_payload(user: object)` to compute:
  - `has_mfa = bool(hasattr(user, 'mfa') and user.mfa and user.mfa.is_enabled)`
  - `mfa_required = bool(is_mfa_required_for_user(user))`
- [ ] **Step 4:** Run pytest again to verify tests pass.
- [ ] **Step 5:** Commit: `feat(accounts): expose mfa status flags in user payload`.

---

### Task 2: Frontend Types & `AuthContext` Support

**Files:**
- Modify: `web/src/api/types.ts`
- Modify: `web/src/auth/AuthContext.tsx`
- Test: `web/src/__tests__/AuthContext.test.tsx` (or auth test suite)

- [ ] **Step 1:** In `web/src/api/types.ts`, add `has_mfa?: boolean;` and `mfa_required?: boolean;` to `User` interface.
- [ ] **Step 2:** In `web/src/auth/AuthContext.tsx`, ensure `setUser` or helper function allows partial updates (e.g., `updateCurrentUser({ has_mfa: true })`) so child components can signal completed 2FA setup immediately.
- [ ] **Step 3:** Run `npm test --prefix web` to verify existing tests continue to pass.
- [ ] **Step 4:** Commit: `feat(web): add mfa flags to user model and auth context`.

---

### Task 3: Build `MFAEnforcementModal` Component

**Files:**
- Create: `web/src/components/MFAEnforcementModal.tsx`
- Create: `web/src/components/MFAEnforcementModal.css`
- Test: `web/src/components/__tests__/MFAEnforcementModal.test.tsx`

- [ ] **Step 1:** Create `MFAEnforcementModal.tsx`:
  - Triggers setup via `authApi.setupMFA()` when user is authenticated with `user.mfa_required && !user.has_mfa`.
  - Renders non-dismissible modal with QR code SVG, manual secret key, 6-digit TOTP input, and submit button.
  - Upon successful verification (`authApi.enableMFA(code)`):
    - Displays list of backup codes with copy-to-clipboard button.
    - Updates user in `AuthContext` (`has_mfa: true`).
    - Provides a "Przejdź do systemu" confirmation button to dismiss the modal.
  - Includes a "Wyloguj się" escape hatch.
- [ ] **Step 2:** Write comprehensive unit tests in `web/src/components/__tests__/MFAEnforcementModal.test.tsx`:
  - Modal renders when user has `mfa_required: true` and `has_mfa: false`.
  - Modal does NOT render when `has_mfa: true`.
  - Displays QR code and accepts 6-digit code.
  - Submits valid code, displays backup codes, and calls update callback.
- [ ] **Step 3:** Run vitest: `npm test --prefix web MFAEnforcementModal`.
- [ ] **Step 4:** Commit: `feat(web): implement mfa enforcement onboarding modal`.

---

### Task 4: Integrate `MFAEnforcementModal` in `AppLayout` and `AdminLayout`

**Files:**
- Modify: `web/src/layouts/AppLayout.tsx`
- Modify: `web/src/layouts/AdminLayout.tsx`
- Test: `web/src/layouts/__tests__/AppLayout.test.tsx`
- Test: `web/src/layouts/__tests__/AdminLayout.test.tsx`

- [ ] **Step 1:** Mount `<MFAEnforcementModal />` in `web/src/layouts/AppLayout.tsx`.
- [ ] **Step 2:** Mount `<MFAEnforcementModal />` in `web/src/layouts/AdminLayout.tsx`.
- [ ] **Step 3:** Update/add tests in `AppLayout.test.tsx` and `AdminLayout.test.tsx`.
- [ ] **Step 4:** Run all web tests and linter: `npm test --prefix web && npm run lint --prefix web`.
- [ ] **Step 5:** Commit: `feat(web): enforce mfa setup in therapist and admin layouts`.

---

### Task 5: Documentation Update

**Files:**
- Modify: `docs/features.md`
- Modify: `docs/test-cases.md`
- Modify: `docs/api.md`

- [ ] **Step 1:** Update `docs/features.md` with section describing mandatory 2FA onboarding for therapists and admins.
- [ ] **Step 2:** Update `docs/test-cases.md` with new test case (e.g. `TC031: Obowiązkowy onboarding 2FA dla personelu medycznego i administratorów`).
- [ ] **Step 3:** Update `docs/api.md` with documentation of `has_mfa` and `mfa_required` in `UserPayload`.
- [ ] **Step 4:** Commit: `docs: document mandatory 2fa onboarding and test cases`.
