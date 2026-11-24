/**
 * @file LocationMapCard.tsx
 * @description Sekcja z podglądem mapy OpenStreetMap i adresem gabinetu/wizyty, umożliwiająca przejście do nawigacji.
 */

import React, { useEffect, useMemo, useState } from 'react'
import { Image, Pressable, StyleSheet, Text, View } from 'react-native'
import { Ionicons } from '@expo/vector-icons'

import { Skeleton } from '@/components/Skeleton'
import { openAddressInMaps } from '@/lib/maps'
import { buildOsmTileGrid, stripPolishPostalCode, TILE_SIZE } from '@/lib/osmMap'
import { colors, radius, space, typography } from '@/theme/tokens'

/** Właściwości komponentu {@link LocationMapCard}. */
interface LocationMapCardProps {
  /** Adres geograficzny do wyświetlenia i geokodowania. */
  address: string
  /** Tytuł nagłówka sekcji (domyślnie "Lokalizacja"). */
  title?: string
}

interface Coords {
  lat: number
  lon: number
}

async function geocodeAddress(query: string): Promise<Coords | null> {
  const url = `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(
    query,
  )}&limit=1`
  const res = await fetch(url, {
    headers: {
      'Accept-Language': 'pl,en',
      'User-Agent': 'PhysioCare-Mobile/1.0',
    },
  })
  if (!res.ok) return null
  const data = (await res.json()) as { lat?: string; lon?: string }[]
  if (Array.isArray(data) && data.length > 0 && data[0]?.lat && data[0]?.lon) {
    const lat = Number.parseFloat(data[0].lat)
    const lon = Number.parseFloat(data[0].lon)
    if (Number.isFinite(lat) && Number.isFinite(lon)) {
      return { lat, lon }
    }
  }
  return null
}

/**
 * Sekcja z podglądem lokalizacji na kafelkach OpenStreetMap oraz przyciskiem otwierającym nawigację w mapach.
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
    setImageError(false)

    if (!trimmed) {
      setCoords(null)
      setLoading(false)
      return
    }

    let isMounted = true
    setLoading(true)

    void (async () => {
      try {
        let found = await geocodeAddress(trimmed)
        if (!found) {
          const fallbackQuery = stripPolishPostalCode(trimmed)
          if (fallbackQuery && fallbackQuery !== trimmed) {
            found = await geocodeAddress(fallbackQuery)
          }
        }
        if (isMounted) {
          setCoords(found)
        }
      } catch (err) {
        console.warn('Mobile geocoding error:', err)
        if (isMounted) {
          setCoords(null)
        }
      } finally {
        if (isMounted) {
          setLoading(false)
        }
      }
    })()

    return () => {
      isMounted = false
    }
  }, [address])

  const tiles = useMemo(() => (coords ? buildOsmTileGrid(coords.lat, coords.lon) : []), [coords])

  if (!address.trim()) {
    return <Text style={styles.emptyText}>Brak podanej lokalizacji.</Text>
  }

  return (
    <Pressable
      style={({ pressed }) => [styles.container, pressed && styles.containerPressed]}
      onPress={() => openAddressInMaps(address)}
      accessibilityRole="link"
      accessibilityLabel={`Otwórz lokalizację ${address} w Mapach`}
      accessibilityHint="Dotknij, aby przejść do nawigacji"
    >
      <View style={styles.headerRow}>
        <Text style={styles.title}>{title}</Text>
        <View style={styles.badge}>
          <Ionicons name="navigate-outline" size={13} color={colors.primary} />
          <Text style={styles.badgeText}>Otwórz w Mapach</Text>
        </View>
      </View>

      <Text style={styles.addressText}>{address}</Text>

      <View style={styles.mapContainer}>
        {loading ? (
          <Skeleton width="100%" height={164} borderRadius={radius.md} />
        ) : tiles.length > 0 && !imageError ? (
          <>
            <View style={styles.mapCenterOrigin} pointerEvents="none">
              {tiles.map((tile) => (
                <Image
                  key={tile.key}
                  source={{
                    uri: tile.url,
                    headers: { 'User-Agent': 'PhysioCare-Mobile/1.0' },
                  }}
                  style={[styles.mapTile, { left: tile.offsetLeft, top: tile.offsetTop }]}
                  resizeMode="cover"
                  onError={() => setImageError(true)}
                />
              ))}
            </View>
            <View style={styles.pinOverlay} pointerEvents="none">
              <Ionicons name="location" size={32} color="#C93B2B" />
            </View>
            <View style={styles.attributionBadge} pointerEvents="none">
              <Text style={styles.attributionText}>© OpenStreetMap</Text>
            </View>
          </>
        ) : (
          <View style={styles.fallbackMap}>
            <Ionicons name="map-outline" size={24} color={colors.primary} />
            <Text style={styles.fallbackText}>Dotknij, aby nawigować do adresu</Text>
          </View>
        )}
      </View>
    </Pressable>
  )
}

const styles = StyleSheet.create({
  container: {
    width: '100%',
  },
  containerPressed: {
    opacity: 0.88,
  },
  headerRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    flexWrap: 'wrap',
    gap: space.sm,
    marginBottom: space.xs,
  },
  title: {
    flexShrink: 1,
    fontSize: typography.xs,
    fontWeight: '700',
    color: colors.muted,
    textTransform: 'uppercase',
    letterSpacing: 0.6,
  },
  badge: {
    flexDirection: 'row',
    alignItems: 'center',
    flexShrink: 0,
    gap: 4,
    backgroundColor: colors.primarySubtle,
    paddingHorizontal: space.sm,
    paddingVertical: 5,
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
    height: 164,
    width: '100%',
    borderRadius: radius.md,
    borderWidth: 1,
    borderColor: colors.border,
    overflow: 'hidden',
    backgroundColor: colors.surfaceMuted,
    position: 'relative',
  },
  mapCenterOrigin: {
    position: 'absolute',
    top: '50%',
    left: '50%',
    width: 0,
    height: 0,
  },
  mapTile: {
    position: 'absolute',
    width: TILE_SIZE,
    height: TILE_SIZE,
  },
  fallbackMap: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: colors.surfaceMuted,
    gap: 6,
  },
  fallbackText: {
    fontSize: typography.xs,
    fontWeight: '600',
    color: colors.muted,
  },
  pinOverlay: {
    position: 'absolute',
    top: '50%',
    left: '50%',
    marginTop: -30,
    marginLeft: -16,
    zIndex: 10,
  },
  attributionBadge: {
    position: 'absolute',
    right: 6,
    bottom: 6,
    backgroundColor: 'rgba(255, 255, 255, 0.85)',
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: radius.sm,
  },
  attributionText: {
    fontSize: 10,
    color: colors.ink,
    fontWeight: '500',
  },
  emptyText: {
    fontSize: typography.sm,
    color: colors.muted,
    fontStyle: 'italic',
  },
})
