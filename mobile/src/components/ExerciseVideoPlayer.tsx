import { useVideoPlayer, VideoView } from 'expo-video'
import { StyleSheet, View } from 'react-native'

import type { AuthenticatedMediaSource } from '@/lib/authMedia'
import { colors, radius } from '@/theme/tokens'

interface ExerciseVideoPlayerProps {
  source: AuthenticatedMediaSource
}

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
        allowsFullscreen
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
