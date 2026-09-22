/**
 * @file maps.ts
 * @description Funkcja pomocnicza do otwierania wskazanego adresu w aplikacji Google Maps / domyślnej nawigacji.
 */

import { Linking } from 'react-native'

/**
 * Otwiera zadaną lokalizację adresową w zewnętrznej aplikacji Google Maps lub przeglądarce.
 *
 * @param address - Adres w postaci tekstowej (np. 'ul. Marszałkowska 10, Warszawa').
 */
export function openAddressInMaps(address: string) {
  const query = address.trim()
  if (!query) {
    return
  }
  const url = `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(query)}`
  void Linking.openURL(url)
}
