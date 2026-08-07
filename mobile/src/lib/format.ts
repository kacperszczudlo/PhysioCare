export function formatDateTime(iso: string): string {
  const date = new Date(iso)
  if (Number.isNaN(date.getTime())) {
    return iso
  }
  return new Intl.DateTimeFormat('pl-PL', {
    weekday: 'short',
    day: 'numeric',
    month: 'short',
    hour: '2-digit',
    minute: '2-digit',
  }).format(date)
}

export function formatDate(iso: string): string {
  const date = new Date(iso)
  if (Number.isNaN(date.getTime())) {
    return iso
  }
  return new Intl.DateTimeFormat('pl-PL', {
    day: 'numeric',
    month: 'long',
    year: 'numeric',
  }).format(date)
}

export function formatTimeRange(startIso: string, endIso: string): string {
  const start = new Date(startIso)
  const end = new Date(endIso)
  if (Number.isNaN(start.getTime()) || Number.isNaN(end.getTime())) {
    return ''
  }
  const fmt = new Intl.DateTimeFormat('pl-PL', {
    hour: '2-digit',
    minute: '2-digit',
  })
  return `${fmt.format(start)}–${fmt.format(end)}`
}

export function todayISODate(): string {
  const now = new Date()
  const y = now.getFullYear()
  const m = String(now.getMonth() + 1).padStart(2, '0')
  const d = String(now.getDate()).padStart(2, '0')
  return `${y}-${m}-${d}`
}

export function addMinutesISO(iso: string, minutes: number): string {
  const date = new Date(iso)
  date.setMinutes(date.getMinutes() + minutes)
  return date.toISOString()
}

export function visitStatusLabel(status: string): string {
  switch (status) {
    case 'PENDING_APPROVAL':
      return 'Oczekuje na zatwierdzenie'
    case 'SCHEDULED':
      return 'Zaplanowana'
    case 'COMPLETED':
      return 'Zakończona'
    case 'CANCELLED':
      return 'Odwołana'
    case 'NO_SHOW':
      return 'Nieobecność'
    default:
      return status
  }
}

export function consentLabel(type: string): string {
  switch (type) {
    case 'TERMS_REQUIRED':
      return 'Regulamin'
    case 'MEDICAL_DATA_REQUIRED':
      return 'Dane medyczne'
    case 'MARKETING_OPTIONAL':
      return 'Marketing'
    case 'RESEARCH_OPTIONAL':
      return 'Badania naukowe'
    default:
      return type
  }
}

export function isRequiredConsent(type: string): boolean {
  return type === 'TERMS_REQUIRED' || type === 'MEDICAL_DATA_REQUIRED'
}

export const DEFAULT_NOTIFICATION_PREFS: Record<string, string> = {
  visit_reminder: 'Przypomnienia o wizytach',
  visit_change: 'Zmiany terminów',
  waitlist: 'Lista rezerwowa',
  exercise_reminder: 'Przypomnienia o ćwiczeniach',
  new_document: 'Nowe dokumenty',
}
