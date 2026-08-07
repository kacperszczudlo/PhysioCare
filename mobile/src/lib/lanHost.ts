import Constants from 'expo-constants'

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
