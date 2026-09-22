/**
 * @file cookies.tsx
 * @description Ekran prezentujący treść polityki plików cookies i technologii w urządzeniu końcowym.
 */

import { LegalDocumentScreen } from '@/components/LegalDocumentScreen'

/**
 * Widok z treścią polityki cookies.
 *
 * @returns Element React Native zawierający dokumentację plików cookies.
 */
export default function CookiesScreen() {
  return <LegalDocumentScreen doc="cookies" />
}
