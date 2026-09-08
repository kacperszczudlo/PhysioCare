import { Image, type ImageStyle, type StyleProp } from 'react-native'

type GoogleMarkProps = {
  size?: number
  style?: StyleProp<ImageStyle>
}

export function GoogleMark({ size = 20, style }: GoogleMarkProps) {
  return (
    <Image
      accessibilityIgnoresInvertColors
      source={require('../../assets/google-logo.png')}
      style={[{ width: size, height: size }, style]}
      resizeMode="contain"
    />
  )
}
