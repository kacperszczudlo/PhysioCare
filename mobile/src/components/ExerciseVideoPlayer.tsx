import { useVideoPlayer, VideoView } from 'expo-video'
import { StyleSheet, View } from 'react-native'

import { colors, radius } from '@/theme/tokens'

interface ExerciseVideoPlayerProps {
  uri: string
}

export function ExerciseVideoPlayer({ uri }: ExerciseVideoPlayerProps) {
  const player = useVideoPlayer(uri, (instance) => {
    instance.loop = false
  })

  return (
    <View style={styles.wrap}>
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
