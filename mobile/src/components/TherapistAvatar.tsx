import { useState } from 'react'
import { Image, StyleSheet, Text, View } from 'react-native'

import { useAuthenticatedCachedUri } from '@/lib/authMedia'
import { colors, typography } from '@/theme/tokens'

interface TherapistAvatarProps {
  /** Adres URL zdjęcia profilowego specjalisty (np. `/media/avatars/...`). */
  avatarUrl?: string | null
  /** Imię specjalisty do wygenerowania inicjałów zapasowych. */
  firstName?: string
  /** Nazwisko specjalisty do wygenerowania inicjałów zapasowych. */
  lastName?: string
  /** Średnica awatara w pikselach (domyślnie 48). */
  size?: number
}

/**
 * Komponent wyświetlający zdjęcie profilowe fizjoterapeuty z autoryzowanym pobieraniem
 * i automatycznym powrotem do inicjałów w przypadku braku zdjęcia lub błędu ładowania.
 */
export function TherapistAvatar({
  avatarUrl,
  firstName = '',
  lastName = '',
  size = 48,
}: TherapistAvatarProps) {
  const [imgFailed, setImgFailed] = useState(false)
  const { uri, error: loadError } = useAuthenticatedCachedUri(avatarUrl)
  const initials = `${firstName?.[0] ?? ''}${lastName?.[0] ?? ''}`.toUpperCase() || '?'
  const showImage = Boolean(uri) && !imgFailed && !loadError
  const borderRadius = size / 2
  const fontSize = size >= 48 ? typography.lg : typography.base

  return (
    <View style={[styles.container, { width: size, height: size, borderRadius }]}>
      {showImage && uri ? (
        <Image
          source={{ uri }}
          style={{ width: size, height: size, borderRadius }}
          resizeMode="cover"
          onError={() => setImgFailed(true)}
          accessibilityIgnoresInvertColors
        />
      ) : (
        <Text style={[styles.initials, { fontSize }]}>{initials}</Text>
      )}
    </View>
  )
}

const styles = StyleSheet.create({
  container: {
    backgroundColor: colors.primarySubtle,
    alignItems: 'center',
    justifyContent: 'center',
    overflow: 'hidden',
  },
  initials: {
    fontWeight: '700',
    color: colors.primary,
  },
})
