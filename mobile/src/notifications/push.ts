import { isRunningInExpoGo } from 'expo'
import Constants from 'expo-constants'
import * as Device from 'expo-device'
import { Platform } from 'react-native'
import type { Router } from 'expo-router'

import { patientApi } from '@/api/patient'
import { tokenStorage } from '@/api/tokenStorage'
import type { DeviceToken } from '@/api/types'

export type PushPermissionStatus = 'granted' | 'denied' | 'undetermined' | 'unsupported'

type NotificationsModule = typeof import('expo-notifications')

function isNative(): boolean {
  return Platform.OS === 'ios' || Platform.OS === 'android'
}

/** Expo Go (SDK 53+) cannot receive Android remote push. */
export function isRemotePushSupported(): boolean {
  return isNative() && !isRunningInExpoGo()
}

async function loadNotifications(): Promise<NotificationsModule | null> {
  if (!isRemotePushSupported()) {
    return null
  }
  return import('expo-notifications')
}

export function configureNotificationHandler(): void {
  if (!isRemotePushSupported()) {
    return
  }
  void loadNotifications().then((NotificationsApi) => {
    NotificationsApi?.setNotificationHandler({
      handleNotification: async () => ({
        shouldShowAlert: true,
        shouldShowBanner: true,
        shouldShowList: true,
        shouldPlaySound: true,
        shouldSetBadge: false,
      }),
    })
  })
}

export function devicePlatform(): DeviceToken['platform'] {
  if (Platform.OS === 'ios') {
    return 'ios'
  }
  if (Platform.OS === 'android') {
    return 'android'
  }
  return 'unknown'
}

export async function getPushPermissionStatus(): Promise<PushPermissionStatus> {
  if (!isNative()) {
    return 'unsupported'
  }
  if (!isRemotePushSupported()) {
    return 'unsupported'
  }
  const NotificationsApi = await loadNotifications()
  if (!NotificationsApi) {
    return 'unsupported'
  }
  const current = await NotificationsApi.getPermissionsAsync()
  if (current.status === 'granted') {
    return 'granted'
  }
  if (current.status === 'denied') {
    return 'denied'
  }
  return 'undetermined'
}

export async function requestPushPermission(): Promise<boolean> {
  if (!isRemotePushSupported()) {
    return false
  }
  const NotificationsApi = await loadNotifications()
  if (!NotificationsApi) {
    return false
  }
  const current = await NotificationsApi.getPermissionsAsync()
  if (current.status === 'granted') {
    return true
  }
  const next = await NotificationsApi.requestPermissionsAsync()
  return next.status === 'granted'
}

async function ensureAndroidChannel(NotificationsApi: NotificationsModule): Promise<void> {
  if (Platform.OS !== 'android') {
    return
  }
  await NotificationsApi.setNotificationChannelAsync('default', {
    name: 'PhysioCare',
    importance: NotificationsApi.AndroidImportance.HIGH,
    vibrationPattern: [0, 250, 250, 250],
    lightColor: '#3D5C32',
  })
}

function expoProjectId(): string | undefined {
  const fromEnv = process.env.EXPO_PUBLIC_EAS_PROJECT_ID?.trim()
  const fromConstants =
    Constants.easConfig?.projectId ??
    (Constants.expoConfig?.extra as { eas?: { projectId?: string } } | undefined)?.eas?.projectId
  // Native APK was built before eas init; Constants.extra.eas is often empty until rebuild.
  return fromEnv || fromConstants || 'ff65be0d-9dc7-4023-a415-66e740d0beb8'
}

export async function getExpoPushToken(): Promise<string | null> {
  if (!isRemotePushSupported() || !Device.isDevice) {
    return null
  }
  const NotificationsApi = await loadNotifications()
  if (!NotificationsApi) {
    return null
  }
  await ensureAndroidChannel(NotificationsApi)
  const granted = await requestPushPermission()
  if (!granted) {
    return null
  }
  const projectId = expoProjectId()
  if (!projectId) {
    console.warn('Brak EAS projectId — nie można pobrać tokenu Expo Push.')
    return null
  }
  const token = await NotificationsApi.getExpoPushTokenAsync({ projectId })
  return token.data
}

export async function registerAndUploadPushToken(): Promise<string | null> {
  if (!isRemotePushSupported()) {
    return null
  }
  try {
    const token = await getExpoPushToken()
    if (!token) {
      return null
    }
    await patientApi.registerDeviceToken(token, devicePlatform())
    await tokenStorage.setPushToken(token)
    return token
  } catch (error) {
    console.warn('Nie udało się zarejestrować powiadomień push', error)
    return null
  }
}

export async function unregisterPushToken(): Promise<void> {
  const token = await tokenStorage.getPushToken()
  if (!token) {
    return
  }
  try {
    await patientApi.unregisterDeviceToken(token)
  } catch (error) {
    console.warn('Nie udało się wyrejestrować tokenu push', error)
  } finally {
    await tokenStorage.clearPushToken()
  }
}

export async function subscribeNotificationResponses(
  onResponse: (data: Record<string, unknown> | undefined) => void,
): Promise<() => void> {
  if (!isRemotePushSupported()) {
    return () => undefined
  }
  const NotificationsApi = await loadNotifications()
  if (!NotificationsApi) {
    return () => undefined
  }

  function handleResponse(response: { notification: { request: { content: { data: unknown } } } } | null) {
    if (!response) {
      return
    }
    const data = response.notification.request.content.data as Record<string, unknown>
    onResponse(data)
  }

  const subscription = NotificationsApi.addNotificationResponseReceivedListener(handleResponse)
  void NotificationsApi.getLastNotificationResponseAsync().then(handleResponse)

  return () => {
    subscription.remove()
  }
}

function asString(value: unknown): string | undefined {
  if (typeof value === 'string' && value.trim()) {
    return value.trim()
  }
  if (typeof value === 'number') {
    return String(value)
  }
  return undefined
}

export function openFromNotificationData(
  router: Pick<Router, 'push'>,
  data: Record<string, unknown> | undefined,
): void {
  if (!data) {
    return
  }
  const type = asString(data.type)
  const id = asString(data.id)
  if (type === 'visit' && id) {
    router.push({ pathname: '/visit/[id]', params: { id } })
    return
  }
  if (type === 'document') {
    router.push('/(tabs)/documents')
    return
  }
  if (type === 'exercise' && id) {
    router.push({ pathname: '/exercise/[id]', params: { id } })
    return
  }
  if (type === 'exercise') {
    router.push('/(tabs)')
  }
}
