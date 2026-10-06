/**
 * @file LocationMapCard.tsx
 * @description Karta z podglądem statycznej mapy i adresem kliniki, umożliwiająca przejście do zewnętrznej nawigacji.
 */

import React, { useEffect, useState } from 'react'
import { Image, Pressable, StyleSheet, Text, View } from 'react-native'
import { Skeleton } from '@/components/Skeleton'
import { openAddressInMaps } from '@/lib/maps'
import { colors, radius, space, typography } from '@/theme/tokens'

/** Właściwości komponentu {@link LocationMapCard}. */
interface LocationMapCardProps {
  /** Adres geograficzny do wyświetlenia i geokodowania. */
  address: string
  /** Tytuł nagłówka karty (domyślnie "Lokalizacja"). */
  title?: string
}

interface Coords {
  lat: number
  lon: number
}

/**
 * Karta z podglądem lokalizacji na mapie OpenStreetMap i przyciskiem otwieranym w natywnej aplikacji map.
 *
 * @param props Właściwości komponentu karty lokalizacji.
 * @returns Element React Native prezentujący mapę i adres.
 */
export const LocationMapCard: React.FC<LocationMapCardProps> = ({
  address,
  title = 'Lokalizacja',
}) => {
  const [coords, setCoords] = useState<Coords | null>(null)
  const [loading, setLoading] = useState(false)
  const [imageError, setImageError] = useState(false)

  useEffect(() => {
    const trimmed = address.trim()
    if (!trimmed) {
      setCoords(null)
      return
    }

    let isMounted = true
    setLoading(true)

    const url = `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(
      trimmed,
    )}&limit=1`

    fetch(url, {
      headers: {
        'Accept-Language': 'pl,en',
        'User-Agent': 'PhysioCare-Mobile/1.0',
      },
    })
      .then((res) => (res.ok ? res.json() : []))
      .then((data) => {
        if (!isMounted) return
        if (Array.isArray(data) && data.length > 0) {
          setCoords({
            lat: parseFloat(data[0].lat),
            lon: parseFloat(data[0].lon),
          })
        }
      })
      .catch((err) => {
        console.warn('Mobile geocoding error:', err)
      })
      .finally(() => {
        if (isMounted) setLoading(false)
      })

    return () => {
      isMounted = false
    }
  }, [address])

  if (!address.trim()) {
    return <Text style={styles.emptyText}>Brak podanej lokalizacji.</Text>
  }

  const staticMapUrl = coords
    ? `https://staticmap.openstreetmap.de/staticmap.php?center=${coords.lat},${coords.lon}&zoom=15&size=600x300&markers=${coords.lat},${coords.lon},ol-marker`
    : null

  return (
    <Pressable
      style={({ pressed }) => [styles.card, pressed && styles.cardPressed]}
      onPress={() => openAddressInMaps(address)}
      accessibilityRole="link"
      accessibilityLabel={`Otwórz lokalizację ${address} w Google Maps`}
      accessibilityHint="Dotknij, aby przejść do nawigacji"
    >
      <View style={styles.headerRow}>
        <Text style={styles.title}>{title}</Text>
        <View style={styles.badge}>
          <Text style={styles.badgeText}>Otwórz w Mapach ➔</Text>
        </View>
      </View>

      <Text style={styles.addressText}>{address}</Text>

      <View style={styles.mapContainer}>
        {loading ? (
          <Skeleton width="100%" height={160} borderRadius={8} />
        ) : staticMapUrl && !imageError ? (
          <Image
            source={{ uri: staticMapUrl }}
            style={styles.mapImage}
            resizeMode="cover"
            onError={() => setImageError(true)}
          />
        ) : (
          <View style={styles.fallbackMap}>
            <Text style={styles.pinIcon}>📍</Text>
            <Text style={styles.fallbackText}>Dotknij, aby nawigować do adresu</Text>
          </View>
        )}

        {staticMapUrl && !imageError && (
          <View style={styles.pinOverlay}>
            <Text style={styles.pinIcon}>📍</Text>
          </View>
        )}
      </View>
    </Pressable>
  )
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: colors.surface,
    borderRadius: radius.lg,
    borderWidth: 1,
    borderColor: colors.border,
    padding: space.md,
    marginTop: space.sm,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.05,
    shadowRadius: 6,
    elevation: 2,
  },
  cardPressed: {
    opacity: 0.92,
    transform: [{ scale: 0.995 }],
  },
  headerRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: space.xs,
  },
  title: {
    fontSize: typography.sm,
    fontWeight: '600',
    color: colors.muted,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  badge: {
    backgroundColor: colors.primarySubtle,
    paddingHorizontal: space.sm,
    paddingVertical: 4,
    borderRadius: 999,
  },
  badgeText: {
    fontSize: typography.xs,
    fontWeight: '700',
    color: colors.primary,
  },
  addressText: {
    fontSize: typography.base,
    fontWeight: '600',
    color: colors.ink,
    marginBottom: space.sm,
    lineHeight: 22,
  },
  mapContainer: {
    height: 140,
    width: '100%',
    borderRadius: radius.md,
    overflow: 'hidden',
    backgroundColor: colors.surfaceMuted,
    position: 'relative',
  },
  mapImage: {
    width: '100%',
    height: '100%',
  },
  loadingContainer: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
  },
  loadingText: {
    fontSize: typography.xs,
    color: colors.muted,
  },
  fallbackMap: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: colors.surfaceMuted,
    gap: 4,
  },
  fallbackText: {
    fontSize: typography.xs,
    fontWeight: '500',
    color: colors.muted,
  },
  pinOverlay: {
    position: 'absolute',
    top: '50%',
    left: '50%',
    marginTop: -16,
    marginLeft: -12,
    zIndex: 10,
  },
  pinIcon: {
    fontSize: 24,
  },
  emptyText: {
    fontSize: typography.sm,
    color: colors.muted,
    fontStyle: 'italic',
  },
})
