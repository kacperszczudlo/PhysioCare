import { Linking } from 'react-native'

export function openAddressInMaps(address: string) {
  const query = address.trim()
  if (!query) {
    return
  }
  const url = `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(query)}`
  void Linking.openURL(url)
}
