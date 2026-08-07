import type { PasswordRequirement } from '@/lib/passwordPolicy'
import { colors, space, typography } from '@/theme/tokens'
import { StyleSheet, Text, View } from 'react-native'

interface PasswordRequirementsProps {
  requirements: PasswordRequirement[]
  /** When true, unmet rules use error color (after submit / blur). */
  showErrors?: boolean
}

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
              <Text style={styles.srOnly}>{req.met ? ' — spełnione' : ' — niespełnione'}</Text>
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
