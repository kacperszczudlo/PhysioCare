import { useRouter } from 'expo-router'
import { useCallback, useEffect, useState } from 'react'
import {
  ActivityIndicator,
  FlatList,
  Pressable,
  RefreshControl,
  StyleSheet,
  Text,
  TextInput,
  View,
} from 'react-native'
import { Ionicons } from '@expo/vector-icons'

import { api, getErrorMessage } from '@/api/client'
import { EmptyState, ErrorBanner, LoadingBlock } from '@/components/AsyncState'
import { MobileTherapistsSkeleton } from '@/components/skeletons/MobileSkeletons'
import { Button } from '@/components/Button'
import { ScreenHeader, SectionCard } from '@/components/ScreenHeader'
import { useToast } from '@/components/ToastContext'
import { colors, controlSize, radius, space, typography } from '@/theme/tokens'

interface Therapist {
  id: string
  first_name: string
  last_name: string
  bio?: string
  avatar_url?: string
  phone?: string
  location_address?: string
  qualification_label?: string
  experience_years?: number
  pwzf_number?: string
}

export default function TherapistsTabScreen() {
  const router = useRouter()
  const { toast } = useToast()

  const [myTherapists, setMyTherapists] = useState<Therapist[]>([])
  const [searchResults, setSearchResults] = useState<Therapist[]>([])
  const [searchQuery, setSearchQuery] = useState('')
  const [loading, setLoading] = useState(true)
  const [searchLoading, setSearchLoading] = useState(false)
  const [linkingId, setLinkingId] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  const loadMyTherapists = useCallback(async () => {
    setError(null)
    try {
      const res = await api.get<Therapist[] | { results: Therapist[] }>('/me/therapists/')
      const items = Array.isArray(res) ? res : res.results || []
      setMyTherapists(items)
    } catch (err) {
      setError(getErrorMessage(err, 'Nie udało się pobrać Twoich fizjoterapeutów.'))
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    void loadMyTherapists()
  }, [loadMyTherapists])

  // Debounced live dynamic search (as user types)
  useEffect(() => {
    const query = searchQuery.trim()
    if (!query) {
      setSearchResults([])
      setSearchLoading(false)
      return
    }

    setSearchLoading(true)
    const timer = setTimeout(async () => {
      try {
        const res = await api.get<Therapist[] | { results: Therapist[] }>(
          `/therapists/public/?search=${encodeURIComponent(query)}`,
        )
        const items = Array.isArray(res) ? res : res.results || []
        setSearchResults(items)
      } catch (err) {
        console.error('Błąd wyszukiwania:', err)
      } finally {
        setSearchLoading(false)
      }
    }, 250)

    return () => {
      clearTimeout(timer)
    }
  }, [searchQuery])

  const handleLinkTherapist = async (therapist: Therapist) => {
    setLinkingId(therapist.id)
    try {
      await api.post('/me/therapists/link/', { therapist_id: therapist.id })
      toast.success(
        'Dodano fizjoterapeutę',
        `${therapist.first_name} ${therapist.last_name} jest teraz na Twojej liście.`,
      )
      void loadMyTherapists()
    } catch (err) {
      toast.error('Błąd dodawania', getErrorMessage(err, 'Nie udało się dodać fizjoterapeuty.'))
    } finally {
      setLinkingId(null)
    }
  }

  const isLinked = (id: string) => myTherapists.some((t) => t.id === id)

  if (loading && myTherapists.length === 0) {
    return (
      <LoadingBlock
        label="Ładowanie listy fizjoterapeutów…"
        skeleton={<MobileTherapistsSkeleton />}
      />
    )
  }

  return (
    <FlatList
      data={myTherapists}
      keyExtractor={(item) => item.id}
      contentContainerStyle={styles.container}
      refreshControl={
        <RefreshControl
          refreshing={loading}
          onRefresh={loadMyTherapists}
          tintColor={colors.primary}
        />
      }
      ListHeaderComponent={
        <View style={styles.headerGap}>
          <ScreenHeader
            title="Specjaliści"
            subtitle="Wyszukaj fizjoterapeutów w bazie i zarządzaj swoją listą."
          />

          {error ? <ErrorBanner message={error} onRetry={loadMyTherapists} /> : null}

          {/* Section: Search catalog */}
          <SectionCard style={styles.searchCard}>
            <Text style={styles.sectionSubtitle}>Wyszukaj specjalistę w bazie</Text>

            <View style={styles.searchRow}>
              <View style={styles.inputWrapper}>
                <Ionicons
                  name="search-outline"
                  size={20}
                  color={colors.muted}
                  style={styles.searchIcon}
                />
                <TextInput
                  style={styles.searchInput}
                  placeholder="Imię, nazwisko, miasto..."
                  placeholderTextColor={colors.muted}
                  value={searchQuery}
                  onChangeText={setSearchQuery}
                  returnKeyType="search"
                />
                {searchLoading ? (
                  <ActivityIndicator size="small" color={colors.primary} />
                ) : searchQuery ? (
                  <Pressable
                    onPress={() => {
                      setSearchQuery('')
                      setSearchResults([])
                    }}
                    hitSlop={8}
                  >
                    <Ionicons name="close-circle" size={18} color={colors.muted} />
                  </Pressable>
                ) : null}
              </View>
            </View>

            {searchResults.length > 0 ? (
              <View style={styles.resultsContainer}>
                <Text style={styles.resultsHeader}>
                  Wyniki wyszukiwania ({searchResults.length}):
                </Text>
                {searchResults.map((item) => {
                  const linked = isLinked(item.id)
                  const isLinking = linkingId === item.id
                  return (
                    <View key={item.id} style={styles.searchResultItem}>
                      <Pressable
                        style={styles.searchResultContent}
                        onPress={() => router.push(`/therapist/${item.id}`)}
                      >
                        <View style={styles.resultAvatar}>
                          <Text style={styles.avatarInitials}>
                            {(item.first_name?.[0] ?? '') + (item.last_name?.[0] ?? '')}
                          </Text>
                        </View>

                        <View style={styles.therapistInfo}>
                          <Text style={styles.therapistName}>
                            {item.first_name} {item.last_name}
                          </Text>
                          {item.qualification_label ? (
                            <Text style={styles.therapistMeta}>{item.qualification_label}</Text>
                          ) : null}
                          {item.location_address ? (
                            <Text style={styles.therapistLoc}>📍 {item.location_address}</Text>
                          ) : null}
                        </View>
                      </Pressable>

                      {!linked ? (
                        <Button
                          title="Dodaj"
                          variant="secondary"
                          loading={isLinking}
                          onPress={() => void handleLinkTherapist(item)}
                          style={styles.linkButton}
                        />
                      ) : null}
                    </View>
                  )
                })}
              </View>
            ) : searchQuery.trim() && !searchLoading ? (
              <View style={styles.noResultsBox}>
                <Ionicons name="search-outline" size={20} color={colors.muted} />
                <Text style={styles.noResultsText}>
                  Brak fizjoterapeutów spełniających kryteria.
                </Text>
              </View>
            ) : null}
          </SectionCard>

          <View style={styles.sectionHeaderRow}>
            <Text style={styles.sectionTitle}>Twoi specjaliści</Text>
            <View style={styles.countBadge}>
              <Text style={styles.countText}>{myTherapists.length}</Text>
            </View>
          </View>
        </View>
      }
      ListEmptyComponent={
        !loading ? (
          <EmptyState
            title="Brak dodanych fizjoterapeutów"
            description="Wyszukaj specjalistę powyżej i dodaj go do swojej listy."
          />
        ) : null
      }
      renderItem={({ item }) => (
        <Pressable onPress={() => router.push(`/therapist/${item.id}`)}>
          <SectionCard style={styles.therapistCard}>
            <View style={styles.cardMainRow}>
              <View style={styles.cardAvatar}>
                <Text style={styles.avatarInitialsLarge}>
                  {(item.first_name?.[0] ?? '') + (item.last_name?.[0] ?? '')}
                </Text>
              </View>
              <View style={styles.cardDetails}>
                <Text style={styles.therapistCardName}>
                  {item.first_name} {item.last_name}
                </Text>
                {item.qualification_label ? (
                  <Text style={styles.therapistCardMeta}>{item.qualification_label}</Text>
                ) : null}
                {item.pwzf_number ? (
                  <Text style={styles.pwzfText}>PWZF: {item.pwzf_number}</Text>
                ) : null}
                {item.location_address ? (
                  <View style={styles.locRow}>
                    <Ionicons name="location-outline" size={14} color={colors.muted} />
                    <Text style={styles.therapistLoc}>{item.location_address}</Text>
                  </View>
                ) : null}
              </View>
              <Ionicons name="chevron-forward" size={20} color={colors.muted} />
            </View>

            {item.bio ? (
              <Text style={styles.bioText} numberOfLines={2}>
                {item.bio}
              </Text>
            ) : null}
          </SectionCard>
        </Pressable>
      )}
    />
  )
}

const styles = StyleSheet.create({
  container: {
    padding: space.base,
    backgroundColor: colors.bg,
  },
  headerGap: {
    gap: space.base,
    marginBottom: space.md,
  },
  searchCard: {
    gap: space.md,
  },
  sectionSubtitle: {
    fontSize: typography.base,
    fontWeight: '700',
    color: colors.ink,
  },
  searchRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: space.sm,
  },
  inputWrapper: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    height: controlSize,
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: radius.md,
    backgroundColor: colors.surface,
    paddingHorizontal: space.md,
    gap: space.xs,
  },
  searchIcon: {
    marginRight: 2,
  },
  searchInput: {
    flex: 1,
    fontSize: typography.base,
    color: colors.ink,
    height: '100%',
  },
  resultsContainer: {
    borderTopWidth: 1,
    borderTopColor: colors.border,
    paddingTop: space.md,
    gap: space.sm,
  },
  resultsHeader: {
    fontSize: typography.sm,
    fontWeight: '600',
    color: colors.muted,
  },
  searchResultItem: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: space.xs,
    gap: space.md,
  },
  searchResultContent: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    gap: space.md,
  },
  resultAvatar: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: colors.primarySubtle,
    alignItems: 'center',
    justifyContent: 'center',
  },
  avatarInitials: {
    fontSize: typography.base,
    fontWeight: '700',
    color: colors.primary,
  },
  therapistInfo: {
    flex: 1,
    gap: 2,
  },
  therapistName: {
    fontSize: typography.base,
    fontWeight: '600',
    color: colors.ink,
  },
  therapistMeta: {
    fontSize: typography.xs,
    color: colors.primary,
    fontWeight: '600',
  },
  therapistLoc: {
    fontSize: typography.xs,
    color: colors.muted,
  },
  linkButton: {
    minHeight: 36,
    paddingHorizontal: space.md,
  },
  sectionHeaderRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: space.xs,
    marginTop: space.xs,
  },
  sectionTitle: {
    fontSize: typography.lg,
    fontWeight: '700',
    color: colors.ink,
  },
  countBadge: {
    backgroundColor: colors.primarySubtle,
    paddingHorizontal: space.sm,
    paddingVertical: 2,
    borderRadius: radius.sm,
  },
  countText: {
    fontSize: typography.xs,
    fontWeight: '700',
    color: colors.primary,
  },
  therapistCard: {
    marginBottom: space.md,
    gap: space.md,
  },
  cardMainRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: space.md,
  },
  cardAvatar: {
    width: 48,
    height: 48,
    borderRadius: 24,
    backgroundColor: colors.primarySubtle,
    alignItems: 'center',
    justifyContent: 'center',
  },
  avatarInitialsLarge: {
    fontSize: typography.lg,
    fontWeight: '700',
    color: colors.primary,
  },
  cardDetails: {
    flex: 1,
    gap: 2,
  },
  therapistCardName: {
    fontSize: typography.base,
    fontWeight: '700',
    color: colors.ink,
  },
  therapistCardMeta: {
    fontSize: typography.sm,
    fontWeight: '600',
    color: colors.primary,
  },
  pwzfText: {
    fontSize: typography.xs,
    color: colors.muted,
  },
  locRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    marginTop: 2,
  },
  bioText: {
    fontSize: typography.sm,
    color: colors.ink,
    lineHeight: 20,
    backgroundColor: colors.bg,
    padding: space.sm,
    borderRadius: radius.sm,
  },
  noResultsBox: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: space.sm,
    paddingVertical: space.md,
    borderTopWidth: 1,
    borderTopColor: colors.border,
    marginTop: space.sm,
  },
  noResultsText: {
    fontSize: typography.sm,
    color: colors.muted,
  },
})
