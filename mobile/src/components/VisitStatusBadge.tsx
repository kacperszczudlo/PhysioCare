import { StyleSheet, Text, View, type TextStyle, type ViewStyle } from 'react-native'

import type { VisitStatus } from '@/api/types'
import { visitStatusLabel } from '@/lib/format'
import { colors, radius, space, typography } from '@/theme/tokens'

interface VisitStatusBadgeProps {
  status: VisitStatus | string
}

export function VisitStatusBadge({ status }: VisitStatusBadgeProps) {
  const label = visitStatusLabel(status)

  let badgeStyle: ViewStyle = styles.badgeDefault
  let textStyle: TextStyle = styles.textDefault

  switch (status) {
    case 'PENDING_APPROVAL':
      badgeStyle = styles.badgePending
      textStyle = styles.textPending
      break
    case 'SCHEDULED':
      badgeStyle = styles.badgeScheduled
      textStyle = styles.textScheduled
      break
    case 'COMPLETED':
      badgeStyle = styles.badgeCompleted
      textStyle = styles.textCompleted
      break
    case 'CANCELLED':
      badgeStyle = styles.badgeCancelled
      textStyle = styles.textCancelled
      break
    case 'NO_SHOW':
      badgeStyle = styles.badgeNoShow
      textStyle = styles.textNoShow
      break
  }

  return (
    <View style={[styles.badge, badgeStyle]}>
      <Text style={[styles.text, textStyle]} numberOfLines={2}>
        {label}
      </Text>
    </View>
  )
}

const styles = StyleSheet.create({
  badge: {
    paddingHorizontal: space.sm,
    paddingVertical: 4,
    borderRadius: radius.sm,
    alignSelf: 'flex-start',
    maxWidth: '56%',
  },
  text: {
    fontSize: typography.xs,
    fontWeight: '700',
    textAlign: 'right',
  },
  badgePending: {
    backgroundColor: colors.accentSubtle,
  },
  textPending: {
    color: colors.warning,
  },
  badgeScheduled: {
    backgroundColor: colors.primarySubtle,
  },
  textScheduled: {
    color: colors.primary,
  },
  badgeCompleted: {
    backgroundColor: colors.successSubtle,
  },
  textCompleted: {
    color: colors.success,
  },
  badgeCancelled: {
    backgroundColor: colors.dangerSubtle,
  },
  textCancelled: {
    color: colors.danger,
  },
  badgeNoShow: {
    backgroundColor: colors.surfaceMuted,
  },
  textNoShow: {
    color: colors.muted,
  },
  badgeDefault: {
    backgroundColor: colors.surfaceMuted,
  },
  textDefault: {
    color: colors.ink,
  },
})
