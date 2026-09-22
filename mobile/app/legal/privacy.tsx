/**
 * @file privacy.tsx
 * @description Ekran prezentujący pełną treść polityki prywatności oraz zasad przetwarzania danych medycznych i osobowych.
 */

import { LegalDocumentScreen } from '@/components/LegalDocumentScreen'

/**
 * Widok z treścią polityki prywatności.
 *
 * @returns Element React Native zawierający dokumentację ochrony prywatności.
 */
export default function PrivacyScreen() {
  return <LegalDocumentScreen doc="privacy" />
}
