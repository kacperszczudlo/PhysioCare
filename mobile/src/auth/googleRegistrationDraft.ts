/** In-memory handoff: Google login → register when account does not exist yet. */

export type GoogleRegistrationDraft = {
  credential: string
  email?: string
  first_name?: string
  last_name?: string
}

let draft: GoogleRegistrationDraft | null = null

export function setGoogleRegistrationDraft(next: GoogleRegistrationDraft | null) {
  draft = next
}

export function takeGoogleRegistrationDraft(): GoogleRegistrationDraft | null {
  const current = draft
  draft = null
  return current
}

export function peekGoogleRegistrationDraft(): GoogleRegistrationDraft | null {
  return draft
}
