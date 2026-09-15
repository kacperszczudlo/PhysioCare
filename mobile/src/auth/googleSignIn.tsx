import { useCallback, useEffect, useState } from 'react'
import {
  ActivityIndicator,
  Platform,
  Pressable,
  StyleSheet,
  Text,
  TurboModuleRegistry,
  View,
} from 'react-native'

import { GoogleMark } from '@/components/GoogleMark'
import { colors, controlSize, radius, space, typography } from '@/theme/tokens'

const webClientId = process.env.EXPO_PUBLIC_GOOGLE_WEB_CLIENT_ID?.trim() ?? ''
const iosClientId = process.env.EXPO_PUBLIC_GOOGLE_IOS_CLIENT_ID?.trim() ?? ''

type GoogleSignInModule = typeof import('@react-native-google-signin/google-signin')

let googleModule: GoogleSignInModule | null | undefined
let configured = false

function hasNativeGoogleSignin(): boolean {
  try {
    return TurboModuleRegistry.get('RNGoogleSignin') != null
  } catch {
    return false
  }
}

function getGoogleModule(): GoogleSignInModule | null {
  if (!hasNativeGoogleSignin()) {
    googleModule = null
    return null
  }
  if (googleModule !== undefined) {
    return googleModule
  }
  try {
    // eslint-disable-next-line @typescript-eslint/no-require-imports
    googleModule = require('@react-native-google-signin/google-signin') as GoogleSignInModule
  } catch {
    googleModule = null
  }
  return googleModule
}

export const isGoogleSignInConfigured = Boolean(webClientId)

export function isGoogleNativeAvailable(): boolean {
  return hasNativeGoogleSignin()
}

function ensureGoogleConfigured() {
  const mod = getGoogleModule()
  if (!mod || configured || !webClientId) {
    return
  }
  mod.GoogleSignin.configure({
    webClientId,
    iosClientId: iosClientId || undefined,
    offlineAccess: false,
  })
  configured = true
}

export async function getGoogleIdToken(): Promise<string> {
  const mod = getGoogleModule()
  if (!webClientId || !mod) {
    throw new Error('Logowanie Google jest chwilowo niedostępne. Użyj e-maila i hasła.')
  }
  ensureGoogleConfigured()

  if (Platform.OS === 'android') {
    await mod.GoogleSignin.hasPlayServices({ showPlayServicesUpdateDialog: true })
  }

  // Force Google native Account Picker modal ("Wybierz konto") every time
  try {
    await mod.GoogleSignin.signOut()
  } catch {
    // Ignore if no active session existed
  }

  const response = await mod.GoogleSignin.signIn()
  if (!mod.isSuccessResponse(response)) {
    throw new Error('Logowanie Google zostało anulowane.')
  }

  const idToken = response.data.idToken
  if (!idToken) {
    throw new Error('Google nie zwróciło tokenu. Sprawdź Web Client ID w konfiguracji.')
  }
  return idToken
}

function mapGoogleError(error: unknown): string {
  const mod = getGoogleModule()
  const raw = error as { code?: string | number; message?: string }
  const code = raw?.code
  const message = typeof raw?.message === 'string' ? raw.message : ''

  // Android OAuth misconfig (SHA-1 / package / webClientId).
  if (
    code === 10 ||
    code === '10' ||
    code === 'DEVELOPER_ERROR' ||
    /DEVELOPER_ERROR/i.test(message) ||
    /Developer console is not set up/i.test(message)
  ) {
    return (
      'Logowanie Google na Androidzie nie jest poprawnie skonfigurowane ' +
      '(SHA-1 debug keystore / pakiet com.physiocare.patient / Web Client ID). ' +
      'Użyj e-maila i hasła albo popraw konfigurację OAuth w Google Cloud.'
    )
  }

  if (mod?.isErrorWithCode(error)) {
    switch (error.code) {
      case mod.statusCodes.SIGN_IN_CANCELLED:
        return 'Logowanie Google zostało anulowane.'
      case mod.statusCodes.IN_PROGRESS:
        return 'Logowanie Google już trwa.'
      case mod.statusCodes.PLAY_SERVICES_NOT_AVAILABLE:
        return 'Usługi Google Play są niedostępne na tym urządzeniu.'
      default:
        return error.message || 'Logowanie Google nie powiodło się.'
    }
  }
  if (error instanceof Error && error.message) {
    return error.message
  }
  return 'Logowanie Google nie powiodło się.'
}

type GoogleSignInButtonProps = {
  loading?: boolean
  disabled?: boolean
  title?: string
  hint?: string
  onBeforePrompt?: () => boolean | Promise<boolean>
  onSuccess: (idToken: string) => void | Promise<void>
  onError: (message: string) => void
}

export function GoogleSignInButton({
  loading = false,
  disabled = false,
  title = 'Kontynuuj z Google',
  hint,
  onBeforePrompt,
  onSuccess,
  onError,
}: GoogleSignInButtonProps) {
  const nativeOk = hasNativeGoogleSignin()
  const [busy, setBusy] = useState(false)
  const isBusy = loading || busy
  const isDisabled = disabled || isBusy

  useEffect(() => {
    if (nativeOk) {
      ensureGoogleConfigured()
    }
  }, [nativeOk])

  const onPress = useCallback(async () => {
    if (onBeforePrompt) {
      const ok = await onBeforePrompt()
      if (!ok) {
        return
      }
    }
    if (!nativeOk) {
      onError('Logowanie Google jest chwilowo niedostępne. Użyj e-maila i hasła.')
      return
    }
    setBusy(true)
    try {
      const idToken = await getGoogleIdToken()
      await onSuccess(idToken)
    } catch (error) {
      onError(mapGoogleError(error))
    } finally {
      setBusy(false)
    }
  }, [onBeforePrompt, nativeOk, onSuccess, onError])

  if (!isGoogleSignInConfigured || !nativeOk) {
    return null
  }

  return (
    <View style={styles.wrap}>
      <Text style={styles.divider}>lub</Text>
      <Pressable
        accessibilityRole="button"
        accessibilityLabel={title}
        accessibilityState={{ disabled: isDisabled, busy: isBusy }}
        disabled={isDisabled}
        onPress={() => {
          void onPress()
        }}
        style={({ pressed }) => [
          styles.button,
          pressed && !isDisabled ? styles.pressed : null,
          isDisabled ? styles.disabled : null,
        ]}
      >
        {isBusy ? (
          <ActivityIndicator color={colors.primary} />
        ) : (
          <View style={styles.row}>
            <GoogleMark size={18} />
            <Text style={styles.label} numberOfLines={1}>
              {title}
            </Text>
          </View>
        )}
      </Pressable>
      {hint ? <Text style={styles.hint}>{hint}</Text> : null}
    </View>
  )
}

const styles = StyleSheet.create({
  wrap: {
    gap: space.md,
    width: '100%',
    alignSelf: 'stretch',
  },
  divider: {
    textAlign: 'center',
    color: colors.muted,
    fontSize: typography.sm,
  },
  button: {
    minHeight: controlSize,
    width: '100%',
    borderRadius: radius.md,
    paddingHorizontal: space.lg,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.borderStrong,
  },
  pressed: {
    backgroundColor: colors.primarySubtle,
  },
  disabled: {
    opacity: 0.55,
  },
  row: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: space.sm,
    maxWidth: '100%',
  },
  label: {
    fontSize: typography.base,
    fontWeight: '600',
    color: colors.ink,
    flexShrink: 1,
  },
  hint: {
    color: colors.muted,
    fontSize: typography.xs,
    textAlign: 'center',
    lineHeight: 18,
  },
})
