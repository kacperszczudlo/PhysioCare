import React, { useEffect, useState } from 'react'
import { ActivityIndicator, Image, Pressable, StyleSheet, Text, View } from 'react-native'
import { openAddressInMaps } from '@/lib/maps'

interface LocationMapCardProps {
  address: string
  title?: string
}

interface Coords {
  lat: number
  lon: number
}

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
          <View style={styles.loadingContainer}>
            <ActivityIndicator size="small" color="#2563eb" />
            <Text style={styles.loadingText}>Ładowanie mapy…</Text>
          </View>
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
    backgroundColor: '#ffffff',
    borderRadius: 14,
    borderWidth: 1,
    borderColor: '#e2e8f0',
    padding: 12,
    marginTop: 8,
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
    marginBottom: 4,
  },
  title: {
    fontSize: 13,
    fontWeight: '600',
    color: '#64748b',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  badge: {
    backgroundColor: '#eff6ff',
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 999,
  },
  badgeText: {
    fontSize: 11,
    fontWeight: '700',
    color: '#2563eb',
  },
  addressText: {
    fontSize: 15,
    fontWeight: '600',
    color: '#0f172a',
    marginBottom: 10,
    lineHeight: 20,
  },
  mapContainer: {
    height: 140,
    width: '100%',
    borderRadius: 10,
    overflow: 'hidden',
    backgroundColor: '#f1f5f9',
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
    fontSize: 12,
    color: '#64748b',
  },
  fallbackMap: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#e2e8f0',
    gap: 4,
  },
  fallbackText: {
    fontSize: 12,
    fontWeight: '500',
    color: '#475569',
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
    fontSize: 14,
    color: '#64748b',
    fontStyle: 'italic',
  },
})
