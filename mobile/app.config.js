const iosClientId = (process.env.EXPO_PUBLIC_GOOGLE_IOS_CLIENT_ID || '').trim()
const iosUrlScheme = iosClientId
  ? `com.googleusercontent.apps.${iosClientId.replace(/\.apps\.googleusercontent\.com$/i, '')}`
  : undefined

/** @type {import('expo/config').ExpoConfig} */
const expoConfig = {
  name: 'PhysioCare',
  slug: 'physiocare',
  version: '0.1.0',
  orientation: 'portrait',
  icon: './assets/icon.png',
  scheme: 'physiocare',
  userInterfaceStyle: 'light',
  newArchEnabled: true,
  splash: {
    image: './assets/splash-icon.png',
    resizeMode: 'contain',
    backgroundColor: '#F4F7F2',
  },
  ios: {
    supportsTablet: true,
    bundleIdentifier: 'com.physiocare.patient',
    infoPlist: {
      UIBackgroundModes: ['remote-notification'],
    },
  },
  android: {
    adaptiveIcon: {
      backgroundColor: '#F4F7F2',
      foregroundImage: './assets/android-icon-foreground.png',
      backgroundImage: './assets/android-icon-background.png',
      monochromeImage: './assets/android-icon-monochrome.png',
    },
    predictiveBackGestureEnabled: false,
    package: 'com.physiocare.patient',
    googleServicesFile: './google-services.json',
    usesCleartextTraffic: true,
    softwareKeyboardLayoutMode: 'resize',
  },
  web: {
    favicon: './assets/favicon.png',
    bundler: 'metro',
  },
  plugins: [
    ['expo-router', { asyncRoutes: false }],
    'expo-secure-store',
    'expo-sharing',
    'expo-status-bar',
    'react-native-quick-crypto',
    'expo-font',
    [
      'expo-image-picker',
      {
        photosPermission: 'PhysioCare potrzebuje dostępu do zdjęć, aby ustawić avatar profilu.',
        cameraPermission: 'PhysioCare potrzebuje dostępu do aparatu, aby zrobić zdjęcie profilowe.',
      },
    ],
    'expo-video',
    [
      'expo-notifications',
      {
        icon: './assets/icon.png',
        color: '#3D5C32',
        defaultChannel: 'default',
      },
    ],
    iosUrlScheme
      ? ['@react-native-google-signin/google-signin', { iosUrlScheme }]
      : '@react-native-google-signin/google-signin',
  ],
  experiments: {
    typedRoutes: true,
  },
  extra: {
    router: {},
    eas: {
      projectId: 'ff65be0d-9dc7-4023-a415-66e740d0beb8',
    },
  },
  owner: 'szczudel',
}

module.exports = { expo: expoConfig }
