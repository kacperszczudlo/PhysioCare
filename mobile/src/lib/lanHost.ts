/**
 * @file lanHost.ts
 * @description Moduł pomocniczy podmieniający adres `localhost` / `127.0.0.1` na IP hosta w lokalnej sieci LAN podczas testowania na fizycznym urządzeniu z Expo.
 */

import Constants from 'expo-constants'

/**
 * Podmienia wystąpienia `localhost` lub `127.0.0.1` na adres IP komputera deweloperskiego pobrany z konfigu Expo.
 *
 * @param url - Surowy adres URL (np. http://localhost:8000/api/v1).
 * @returns Przeprowadzony URL z adresem LAN (np. http://192.168.1.50:8000/api/v1).
 */
export function rewriteLocalhostToLan(url: string): string {
  if (!/localhost|127\.0\.0\.1/i.test(url)) {
    return url
  }
  const hostUri = Constants.expoConfig?.hostUri
  if (!hostUri) {
    return url
  }
  const lanHost = hostUri.split(':')[0]
  if (!lanHost || /^(localhost|127\.0\.0\.1)$/i.test(lanHost)) {
    return url
  }
  return url.replace(/localhost|127\.0\.0\.1/gi, lanHost)
}
