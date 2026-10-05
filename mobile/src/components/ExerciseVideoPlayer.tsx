/**
 * @file ExerciseVideoPlayer.tsx
 * @description Komponent odtwarzacza wideo dla ćwiczeń z obsługą uwierzytelnionych źródeł mediów.
 */

import { useVideoPlayer, VideoView } from 'expo-video'
import { StyleSheet, View } from 'react-native'

import type { AuthenticatedMediaSource } from '@/lib/authMedia'
import { colors, radius } from '@/theme/tokens'

/** Właściwości komponentu {@link ExerciseVideoPlayer}. */
interface ExerciseVideoPlayerProps {
  /** Uwierzytelnione źródło pliku wideo (URI oraz opcjonalne nagłówki auth). */
  source: AuthenticatedMediaSource
}

/**
 * Odtwarzacz wideo instruktażowego do ćwiczeń rehabilitacyjnych.
 *
 * @param props Właściwości komponentu odtwarzacza wideo.
 * @returns Element React Native zawierający odtwarzacz VideoView.
 */
export function ExerciseVideoPlayer({ source }: ExerciseVideoPlayerProps) {
  const player = useVideoPlayer(source, (instance) => {
    instance.loop = false
  })

  return (
    <View style={styles.wrap} key={source.uri}>
      <VideoView
        style={styles.video}
        player={player}
        nativeControls
        contentFit="contain"
        fullscreenOptions={{ enable: true }}
        allowsPictureInPicture
      />
    </View>
  )
}

const styles = StyleSheet.create({
  wrap: {
    width: '100%',
    borderRadius: radius.md,
    overflow: 'hidden',
    backgroundColor: '#1a2218',
    borderWidth: 1,
    borderColor: colors.border,
  },
  video: {
    width: '100%',
    aspectRatio: 16 / 10,
    backgroundColor: '#1a2218',
  },
})
