import { StyleSheet, Text, View } from 'react-native'
import { useSafeAreaInsets } from 'react-native-safe-area-context'

import { useNetwork } from '@/network/NetworkContext'
import { colors, space, typography } from '@/theme/tokens'

export function OfflineBanner() {
  const { isOffline, isResolved } = useNetwork()
  const insets = useSafeAreaInsets()

  if (!isResolved || !isOffline) {
    return null
  }

  return (
    <View
      style={[styles.banner, { paddingTop: Math.max(insets.top, space.sm) }]}
      accessibilityRole="alert"
      accessibilityLiveRegion="polite"
    >
      <Text style={styles.title}>Brak połączenia z internetem</Text>
      <Text style={styles.subtitle}>
        Niektóre dane mogą być niedostępne. Sprawdź sieć i spróbuj ponownie.
      </Text>
    </View>
  )
}

const styles = StyleSheet.create({
  banner: {
    backgroundColor: colors.warning,
    paddingHorizontal: space.base,
    paddingBottom: space.sm,
    gap: 2,
  },
  title: {
    color: colors.onPrimary,
    fontSize: typography.sm,
    fontWeight: '700',
    textAlign: 'center',
  },
  subtitle: {
    color: colors.onPrimary,
    fontSize: typography.xs,
    textAlign: 'center',
    opacity: 0.92,
  },
})
