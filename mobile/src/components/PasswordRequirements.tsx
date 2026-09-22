/**
 * @file PasswordRequirements.tsx
 * @description Listowanie kryteriów bezpieczeństwa hasła (długość, cyfry, znaki specjalne) z dynamicznym wskaźnikiem ich spełnienia.
 */

import type { PasswordRequirement } from '@/lib/passwordPolicy'
import { colors, space, typography } from '@/theme/tokens'
import { StyleSheet, Text, View } from 'react-native'

/** Właściwości komponentu {@link PasswordRequirements}. */
interface PasswordRequirementsProps {
  /** Lista wymogów bezpieczeństwa hasła wraz ze stanem ich spełnienia. */
  requirements: PasswordRequirement[]
  /** Czy wymuszać wyświetlanie błędów dla niespełnionych wymogów. */
  showErrors?: boolean
}

/**
 * Komponent wizualizujący checklistę wymagań dotyczących haseł (np. 8+ znaków, duża litera).
 *
 * @param props Właściwości listy wymagań.
 * @returns Element React Native prezentujący checklistę.
 */
export function PasswordRequirements({
  requirements,
  showErrors = false,
}: PasswordRequirementsProps) {
  return (
    <View accessibilityLabel="Wymagania hasła" style={styles.list}>
      {requirements.map((req) => {
        const state = req.met ? 'met' : showErrors ? 'fail' : 'pending'
        const color =
          state === 'met' ? colors.success : state === 'fail' ? colors.danger : colors.muted
        return (
          <View key={req.id} style={styles.item}>
            <Text style={[styles.mark, { color }]} accessibilityElementsHidden>
              {req.met ? '✓' : '○'}
            </Text>
            <Text style={[styles.label, { color }]}>
              {req.label}
              <Text style={styles.srOnly}>{req.met ? ' - spełnione' : ' - niespełnione'}</Text>
            </Text>
          </View>
        )
      })}
    </View>
  )
}

const styles = StyleSheet.create({
  list: { gap: space.sm },
  item: { flexDirection: 'row', alignItems: 'flex-start', gap: space.sm },
  mark: { fontSize: typography.sm, fontWeight: '700', lineHeight: 20 },
  label: { flex: 1, fontSize: typography.sm, lineHeight: 20 },
  srOnly: { width: 0, height: 0, opacity: 0 },
})
