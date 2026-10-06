/**
 * @file [id].tsx
 * @description Ekran profilu publicznego fizjoterapeuty (biogram, kwalifikacje, uprawnienia, kursy, mapa i kontakt).
 */

import { Stack, useLocalSearchParams } from 'expo-router'
import { useCallback, useEffect, useMemo, useState } from 'react'
import { Alert, Image, Linking, Pressable, ScrollView, StyleSheet, Text, View } from 'react-native'
import { Ionicons } from '@expo/vector-icons'

import { api, getErrorMessage } from '@/api/client'
import { patientApi } from '@/api/patient'
import type { RatingSummary, ReviewItem, TherapistPublic } from '@/api/types'
import { ErrorBanner, LoadingBlock } from '@/components/AsyncState'
import { MobileTherapistDetailSkeleton } from '@/components/skeletons/MobileSkeletons'
import { Button } from '@/components/Button'
import { SectionCard } from '@/components/ScreenHeader'
import { LocationMapCard } from '@/components/LocationMapCard'
import { ReviewModal } from '@/components/ReviewModal'
import { useToast } from '@/components/ToastContext'
import { useAuthenticatedCachedUri } from '@/lib/authMedia'
import { formatDateTime } from '@/lib/format'
import { colors, radius, space, typography } from '@/theme/tokens'

function yearsLabel(years: number): string {
  if (years === 1) {
    return '1 rok stażu'
  }
  if (years >= 2 && years <= 4) {
    return `${years} lata stażu`
  }
  return `${years} lat stażu`
}

function getInitials(name: string): string {
  const parts = name.trim().split(/\s+/).filter(Boolean)
  if (parts.length === 0) return '?'
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase()
  return (parts[0][0] + parts[1][0]).toUpperCase()
}

function ReviewAuthorAvatar({ item }: { item: ReviewItem }) {
  const [imgFailed, setImgFailed] = useState(false)
  const shouldFetch = !item.is_anonymous && Boolean(item.author_avatar_url)
  const { uri, error: loadError } = useAuthenticatedCachedUri(
    shouldFetch ? item.author_avatar_url : null,
  )

  if (item.is_anonymous) {
    return (
      <View style={styles.reviewAvatarAnon} accessibilityLabel="Anonimowy pacjent">
        <Ionicons name="person" size={16} color={colors.muted} />
      </View>
    )
  }

  const showImg = Boolean(uri) && !imgFailed && !loadError
  if (showImg && uri) {
    return (
      <View style={styles.reviewAvatarClip}>
        <Image source={{ uri }} style={styles.reviewAvatarImg} onError={() => setImgFailed(true)} />
      </View>
    )
  }

  return (
    <View style={styles.reviewAvatarInitials} accessibilityLabel={item.author_name}>
      <Text style={styles.reviewAvatarInitialsText}>{getInitials(item.author_name)}</Text>
    </View>
  )
}

/**
 * Ekran wizytówki publicznej fizjoterapeuty z przyciskiem powiązania z kontem pacjenta.
 *
 * @returns Element React Native prezentujący profil specjalisty.
 */
export default function TherapistPublicScreen() {
  const { toast } = useToast()
  const { id } = useLocalSearchParams<{ id: string }>()

  const [therapist, setTherapist] = useState<TherapistPublic | null>(null)
  const [reviews, setReviews] = useState<ReviewItem[]>([])
  const [ratingSummary, setRatingSummary] = useState<RatingSummary | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [avatarFailed, setAvatarFailed] = useState(false)
  const [expandedCode, setExpandedCode] = useState<string | null>(null)
  const [isLinked, setIsLinked] = useState(false)
  const [linking, setLinking] = useState(false)
  const [reviewModalOpen, setReviewModalOpen] = useState(false)
  const [editingReview, setEditingReview] = useState<ReviewItem | null>(null)
  const [selectedRatingFilter, setSelectedRatingFilter] = useState<number | null>(null)
  const [selectedOrdering, setSelectedOrdering] = useState<'-created_at' | '-rating' | 'rating'>(
    '-created_at',
  )
  const [reviewsExpanded, setReviewsExpanded] = useState(false)

  const { uri: avatarUri, error: avatarLoadError } = useAuthenticatedCachedUri(
    therapist?.avatar_url,
  )

  const load = useCallback(async () => {
    if (!id) {
      return
    }
    setError(null)
    setLoading(true)
    try {
      const [tData, myRes, revs, summary] = await Promise.all([
        patientApi.getTherapistPublic(id),
        api.get<TherapistPublic[] | { results: TherapistPublic[] }>('/me/therapists/'),
        patientApi
          .getTherapistReviews(id, selectedRatingFilter ?? undefined, selectedOrdering)
          .catch(() => []),
        patientApi.getTherapistRatingSummary(id).catch(() => null),
      ])
      const myItems = Array.isArray(myRes) ? myRes : myRes.results || []
      setTherapist(tData)
      setIsLinked(myItems.some((item) => item.id === id))
      setReviews(revs)
      setRatingSummary(summary)
      setAvatarFailed(false)
    } catch (err) {
      setError(getErrorMessage(err, 'Nie udało się pobrać profilu terapeuty.'))
    } finally {
      setLoading(false)
    }
  }, [id, selectedRatingFilter, selectedOrdering])

  useEffect(() => {
    void load()
  }, [load])

  const handleLink = async () => {
    if (!therapist) return
    setLinking(true)
    try {
      await api.post('/me/therapists/link/', { therapist_id: therapist.id })
      setIsLinked(true)
      toast.success(
        'Dodano specjalistę',
        `${therapist.first_name} ${therapist.last_name} został dodany do Twoich specjalistów.`,
      )
    } catch (err) {
      toast.error('Błąd dodawania', getErrorMessage(err, 'Nie udało się dodać fizjoterapeuty.'))
    } finally {
      setLinking(false)
    }
  }

  const allowed = useMemo(
    () => therapist?.competences?.capabilities.filter((cap) => cap.allowed) ?? [],
    [therapist],
  )

  const ownReview = useMemo(() => reviews.find((r) => r.is_own), [reviews])

  const DISPLAY_LIMIT = 3
  const displayedReviews = useMemo(() => {
    if (reviewsExpanded) {
      return reviews
    }
    return reviews.slice(0, DISPLAY_LIMIT)
  }, [reviews, reviewsExpanded])

  const handleReviewSubmit = async (data: {
    rating: number
    comment: string
    is_anonymous: boolean
  }) => {
    if (!therapist) return
    if (editingReview) {
      await patientApi.editReview(editingReview.id, data)
      toast.success('Zaktualizowano opinię')
    } else {
      await patientApi.createTherapistReview(therapist.id, data)
      toast.success('Dziękujemy!', 'Twoja opinia została dodana.')
    }
    void load()
  }

  const handleDeleteReview = (reviewId: string) => {
    Alert.alert('Usunąć opinię?', 'Czy na pewno chcesz usunąć swoją opinię?', [
      { text: 'Anuluj', style: 'cancel' },
      {
        text: 'Usuń',
        style: 'destructive',
        onPress: async () => {
          try {
            await patientApi.deleteReview(reviewId)
            toast.success('Opinia usunięta')
            void load()
          } catch (err) {
            toast.error('Błąd', getErrorMessage(err, 'Nie udało się usunąć opinii.'))
          }
        },
      },
    ])
  }

  if (loading) {
    return <LoadingBlock skeleton={<MobileTherapistDetailSkeleton />} />
  }

  if (!therapist) {
    return (
      <View style={styles.pad}>
        <ErrorBanner message={error ?? 'Nie znaleziono terapeuty.'} onRetry={() => void load()} />
      </View>
    )
  }

  const fullName = `${therapist.first_name} ${therapist.last_name}`
  const initials =
    `${therapist.first_name?.[0] ?? ''}${therapist.last_name?.[0] ?? ''}`.toUpperCase()
  const showAvatar = Boolean(avatarUri) && !avatarFailed && !avatarLoadError
  const qualification =
    therapist.qualification_label ?? therapist.competences?.qualification_label ?? null
  const experienceYears =
    therapist.experience_years ?? therapist.competences?.experience_years ?? null
  const avgRating = ratingSummary?.average_rating ?? therapist.rating_avg ?? 0
  const countReviews = ratingSummary?.total_reviews ?? therapist.rating_count ?? 0

  return (
    <>
      <Stack.Screen options={{ title: fullName }} />
      <ScrollView style={styles.flex} contentContainerStyle={styles.content}>
        {error ? <ErrorBanner message={error} onRetry={() => void load()} /> : null}

        <SectionCard>
          <View style={styles.hero}>
            {showAvatar ? (
              <View style={styles.avatarClip}>
                <Image
                  source={{ uri: avatarUri! }}
                  style={styles.avatar}
                  resizeMode="cover"
                  onError={() => setAvatarFailed(true)}
                  accessibilityIgnoresInvertColors
                />
              </View>
            ) : (
              <View style={[styles.avatar, styles.avatarPlaceholder]}>
                <Text style={styles.initials}>{initials || '?'}</Text>
              </View>
            )}
            <View style={styles.heroText}>
              <Text style={styles.name}>{fullName}</Text>
              {Number(countReviews) > 0 ? (
                <View style={styles.ratingBadge}>
                  <Text style={styles.ratingStars}>★</Text>
                  <Text style={styles.ratingScore}>{Number(avgRating).toFixed(1)}</Text>
                  <Text style={styles.ratingCount}>
                    ({countReviews} {countReviews === 1 ? 'opinia' : 'opinii'})
                  </Text>
                </View>
              ) : (
                <Text style={styles.noRatingText}>Brak ocen (nowy specjalista)</Text>
              )}
              {qualification ? <Text style={styles.qualification}>{qualification}</Text> : null}
              {experienceYears != null ? (
                <Text style={styles.muted}>{yearsLabel(experienceYears)}</Text>
              ) : null}
              {therapist.pwzf_number ? (
                <Text style={styles.pwzfText}>PWZF: {therapist.pwzf_number}</Text>
              ) : null}
              <Text style={styles.bio}>{therapist.bio || 'Brak biogramu.'}</Text>
            </View>
          </View>

          {!isLinked ? (
            <View style={styles.actionRow}>
              <Button
                title="Dodaj do moich specjalistów"
                variant="secondary"
                loading={linking}
                onPress={() => void handleLink()}
              />
            </View>
          ) : null}
        </SectionCard>

        {therapist.competences ? (
          <SectionCard>
            <Text style={styles.section}>Uprawnienia</Text>
            <Text style={styles.muted}>
              {qualification ?? 'Fizjoterapeuta'}
              {experienceYears != null ? ` · ${yearsLabel(experienceYears)}` : ''}
            </Text>

            {therapist.competences.can_plan_therapy ||
            therapist.competences.can_supervise ||
            therapist.competences.is_fizjo_spec ||
            therapist.competences.device_groups.length > 0 ? (
              <View style={styles.chipRow}>
                {therapist.competences.can_plan_therapy ? (
                  <Text style={[styles.chip, styles.chipOk]}>Planowanie terapii</Text>
                ) : null}
                {therapist.competences.can_supervise ? (
                  <Text style={[styles.chip, styles.chipOk]}>Nadzór</Text>
                ) : null}
                {therapist.competences.is_fizjo_spec ? (
                  <Text style={[styles.chip, styles.chipOk]}>FIZJO SPEC</Text>
                ) : null}
                {therapist.competences.device_groups.length > 0 ? (
                  <Text style={[styles.chip, styles.chipOk]}>
                    Wyroby: {therapist.competences.device_groups.join(', ')}
                  </Text>
                ) : null}
              </View>
            ) : null}

            {allowed.length === 0 ? (
              <Text style={styles.muted}>Brak dodatkowych uprawnień w profilu.</Text>
            ) : (
              allowed.map((cap) => {
                const open = expandedCode === cap.code
                return (
                  <Pressable
                    key={cap.code}
                    onPress={() => setExpandedCode(open ? null : cap.code)}
                    accessibilityRole="button"
                    accessibilityState={{ expanded: open }}
                    style={styles.capRow}
                  >
                    <View style={styles.capHead}>
                      <Text style={styles.capLabel}>{cap.label}</Text>
                      <Text style={styles.capToggle}>{open ? '−' : '+'}</Text>
                    </View>
                    {open ? <Text style={styles.capDetail}>{cap.detail}</Text> : null}
                  </Pressable>
                )
              })
            )}
          </SectionCard>
        ) : null}

        <SectionCard>
          <Text style={styles.section}>Kursy i certyfikaty</Text>
          {(therapist.courses ?? []).length === 0 ? (
            <Text style={styles.muted}>Brak wpisów.</Text>
          ) : (
            therapist.courses.map((course) => (
              <Text key={course} style={styles.course}>
                · {course}
              </Text>
            ))
          )}
        </SectionCard>

        <SectionCard>
          <LocationMapCard
            address={therapist.location_address || ''}
            title="Lokalizacja gabinetu"
          />
        </SectionCard>

        <SectionCard>
          <View style={styles.reviewsTitleRow}>
            <View style={styles.reviewsTitleTextWrap}>
              <Text style={styles.section}>Opinie pacjentów</Text>
              {Number(countReviews) > 0 ? (
                <Text style={styles.muted}>
                  Średnia: {Number(avgRating).toFixed(1)} / 5.0 ({countReviews})
                </Text>
              ) : (
                <Text style={styles.muted}>Ten fizjoterapeuta nie ma jeszcze opinii.</Text>
              )}
            </View>
            <Button
              title={ownReview ? 'Edytuj opinię' : '★ Dodaj opinię'}
              variant={ownReview ? 'secondary' : 'primary'}
              onPress={() => {
                if (ownReview) {
                  setEditingReview(ownReview)
                } else {
                  setEditingReview(null)
                }
                setReviewModalOpen(true)
              }}
              style={styles.addReviewBtn}
            />
          </View>

          {/* Breakdown ocen — klikalny filtr */}
          {ratingSummary && ratingSummary.total_reviews > 0 ? (
            <View style={styles.breakdownCard}>
              {[5, 4, 3, 2, 1].map((stars) => {
                const count = ratingSummary.rating_breakdown[stars] ?? 0
                const percent =
                  ratingSummary.total_reviews > 0 ? (count / ratingSummary.total_reviews) * 100 : 0
                const isSelected = selectedRatingFilter === stars
                return (
                  <Pressable
                    key={stars}
                    style={[styles.breakdownRow, isSelected && styles.breakdownRowSelected]}
                    onPress={() => {
                      setSelectedRatingFilter((prev) => (prev === stars ? null : stars))
                      setReviewsExpanded(false)
                    }}
                    hitSlop={{ top: 8, bottom: 8, left: 4, right: 4 }}
                    accessibilityRole="button"
                    accessibilityState={{ selected: isSelected }}
                    accessibilityLabel={`Filtruj oceny: ${stars} gwiazdek, ${count} opinii`}
                    accessibilityHint="Dotknij, aby przełączyć filtr dla tej liczby gwiazdek"
                  >
                    <Text
                      style={[styles.breakdownStars, isSelected && styles.breakdownStarsSelected]}
                    >
                      {stars} ★
                    </Text>
                    <View style={styles.barTrack}>
                      <View style={[styles.barFill, { width: `${percent}%` }]} />
                    </View>
                    <Text
                      style={[styles.breakdownCount, isSelected && styles.breakdownCountSelected]}
                    >
                      {count}
                    </Text>
                  </Pressable>
                )
              })}
            </View>
          ) : null}

          {/* Aktywny filtr ocen */}
          {selectedRatingFilter !== null ? (
            <View style={styles.activeFilterRow}>
              <Text style={styles.activeFilterText}>
                Filtrujesz oceny: <Text style={styles.bold}>{selectedRatingFilter} ★</Text>
              </Text>
              <Pressable
                onPress={() => {
                  setSelectedRatingFilter(null)
                  setReviewsExpanded(false)
                }}
                style={styles.clearFilterBtn}
                hitSlop={{ top: 12, bottom: 12, left: 12, right: 12 }}
                accessibilityRole="button"
                accessibilityLabel="Wyczyść filtr ocen"
                accessibilityHint="Usuwa aktywny filtr ocen i pokazuje wszystkie opinie"
              >
                <Text style={styles.clearFilterText}>Wyczyść filtr ✕</Text>
              </Pressable>
            </View>
          ) : null}

          {/* Pasek sortowania */}
          {ratingSummary && ratingSummary.total_reviews > 0 ? (
            <View style={styles.reviewSortRow}>
              <Text style={styles.reviewSortLabel}>Sortuj:</Text>
              <ScrollView
                horizontal
                showsHorizontalScrollIndicator={false}
                contentContainerStyle={styles.sortChipsWrap}
              >
                <Pressable
                  style={[
                    styles.sortChip,
                    selectedOrdering === '-created_at' && styles.sortChipActive,
                  ]}
                  onPress={() => setSelectedOrdering('-created_at')}
                  accessibilityRole="button"
                  accessibilityState={{ selected: selectedOrdering === '-created_at' }}
                  accessibilityLabel="Sortuj: Najnowsze"
                  hitSlop={{ top: 6, bottom: 6, left: 4, right: 4 }}
                >
                  <Ionicons
                    name="time-outline"
                    size={13}
                    color={selectedOrdering === '-created_at' ? colors.onPrimary : colors.muted}
                  />
                  <Text
                    style={[
                      styles.sortChipText,
                      selectedOrdering === '-created_at' && styles.sortChipTextActive,
                    ]}
                  >
                    Najnowsze
                  </Text>
                </Pressable>

                <Pressable
                  style={[styles.sortChip, selectedOrdering === '-rating' && styles.sortChipActive]}
                  onPress={() => setSelectedOrdering('-rating')}
                  accessibilityRole="button"
                  accessibilityState={{ selected: selectedOrdering === '-rating' }}
                  accessibilityLabel="Sortuj: Najwyższe oceny"
                  hitSlop={{ top: 6, bottom: 6, left: 4, right: 4 }}
                >
                  <Ionicons
                    name="star"
                    size={13}
                    color={selectedOrdering === '-rating' ? colors.onPrimary : colors.muted}
                  />
                  <Text
                    style={[
                      styles.sortChipText,
                      selectedOrdering === '-rating' && styles.sortChipTextActive,
                    ]}
                  >
                    Najwyższe oceny
                  </Text>
                </Pressable>

                <Pressable
                  style={[styles.sortChip, selectedOrdering === 'rating' && styles.sortChipActive]}
                  onPress={() => setSelectedOrdering('rating')}
                  accessibilityRole="button"
                  accessibilityState={{ selected: selectedOrdering === 'rating' }}
                  accessibilityLabel="Sortuj: Najniższe oceny"
                  hitSlop={{ top: 6, bottom: 6, left: 4, right: 4 }}
                >
                  <Ionicons
                    name="arrow-down-outline"
                    size={13}
                    color={selectedOrdering === 'rating' ? colors.onPrimary : colors.muted}
                  />
                  <Text
                    style={[
                      styles.sortChipText,
                      selectedOrdering === 'rating' && styles.sortChipTextActive,
                    ]}
                  >
                    Najniższe oceny
                  </Text>
                </Pressable>
              </ScrollView>
            </View>
          ) : null}

          {/* Lista opinii */}
          {displayedReviews.length > 0 ? (
            <View style={styles.reviewList}>
              {displayedReviews.map((rev) => (
                <View key={rev.id} style={[styles.reviewCard, rev.is_own && styles.reviewCardOwn]}>
                  <View style={styles.reviewCardHead}>
                    <View style={styles.reviewAuthorRow}>
                      <ReviewAuthorAvatar item={rev} />
                      <View style={styles.reviewAuthorCol}>
                        <View style={styles.nameAndBadgeWrap}>
                          <Text style={styles.authorName}>{rev.author_name}</Text>
                          {rev.is_own ? (
                            <View style={styles.ownReviewBadge}>
                              <Text style={styles.ownReviewText}>Twoja opinia</Text>
                            </View>
                          ) : null}
                        </View>
                        {rev.is_verified ? (
                          <View style={styles.verifiedBadge}>
                            <Ionicons name="checkmark-circle" size={14} color={colors.primary} />
                            <Text style={styles.verifiedText}>Zweryfikowana wizyta</Text>
                          </View>
                        ) : null}
                      </View>
                    </View>
                    <View style={styles.reviewScoreCol}>
                      <Text style={styles.reviewStars}>
                        {'★'.repeat(rev.rating)}
                        {'☆'.repeat(5 - rev.rating)}
                      </Text>
                      <Text style={styles.reviewDate}>{formatDateTime(rev.created_at)}</Text>
                    </View>
                  </View>

                  {rev.comment ? <Text style={styles.reviewComment}>{rev.comment}</Text> : null}

                  {rev.therapist_reply ? (
                    <View style={styles.replyBox}>
                      <View style={styles.replyHeaderRow}>
                        <View style={styles.replyAvatarWrap}>
                          {showAvatar && avatarUri ? (
                            <Image
                              source={{ uri: avatarUri }}
                              style={styles.replyAvatarImg}
                              resizeMode="cover"
                            />
                          ) : (
                            <View style={styles.replyAvatarInitials}>
                              <Text style={styles.replyAvatarInitialsText}>{initials || 'FT'}</Text>
                            </View>
                          )}
                        </View>
                        <View style={styles.replyMetaCol}>
                          <View style={styles.replyAuthorNameRow}>
                            <Text style={styles.replyAuthorName}>{fullName}</Text>
                            <View style={styles.replyRoleBadge}>
                              <Text style={styles.replyRoleBadgeText}>Fizjoterapeuta</Text>
                            </View>
                          </View>
                          {rev.therapist_replied_at ? (
                            <Text style={styles.replyDate}>
                              {formatDateTime(rev.therapist_replied_at)}
                            </Text>
                          ) : null}
                        </View>
                      </View>
                      <Text style={styles.replyComment}>{rev.therapist_reply}</Text>
                    </View>
                  ) : null}

                  {rev.is_own ? (
                    <View style={styles.reviewOwnActions}>
                      <Button
                        title="Edytuj"
                        variant="secondary"
                        onPress={() => {
                          setEditingReview(rev)
                          setReviewModalOpen(true)
                        }}
                      />
                      <Button
                        title="Usuń"
                        variant="danger"
                        onPress={() => handleDeleteReview(rev.id)}
                      />
                    </View>
                  ) : null}
                </View>
              ))}

              {reviews.length > DISPLAY_LIMIT ? (
                <Button
                  title={
                    reviewsExpanded ? 'Zwiń opinie' : `Zobacz wszystkie opinie (${reviews.length})`
                  }
                  variant="secondary"
                  onPress={() => setReviewsExpanded((prev) => !prev)}
                  style={styles.expandReviewsBtn}
                />
              ) : null}
            </View>
          ) : selectedRatingFilter !== null ? (
            <View style={styles.emptyFilteredReviews}>
              <Text style={styles.muted}>Brak opinii z oceną {selectedRatingFilter} ★.</Text>
              <Button
                title="Pokaż wszystkie opinie"
                variant="secondary"
                onPress={() => {
                  setSelectedRatingFilter(null)
                  setReviewsExpanded(false)
                }}
                style={{ marginTop: space.sm }}
              />
            </View>
          ) : null}
        </SectionCard>

        <SectionCard>
          <Text style={styles.section}>Kontakt</Text>
          <Button
            title="Zadzwoń"
            disabled={!therapist.phone}
            onPress={() => {
              if (therapist.phone) {
                void Linking.openURL(`tel:${therapist.phone}`)
              }
            }}
          />
          <Button
            title="Napisz SMS"
            variant="secondary"
            disabled={!therapist.phone}
            onPress={() => {
              if (therapist.phone) {
                void Linking.openURL(`sms:${therapist.phone}`)
              }
            }}
          />
          {!therapist.phone ? (
            <Text style={styles.muted}>Terapeuta nie podał numeru telefonu.</Text>
          ) : null}
        </SectionCard>
      </ScrollView>

      <ReviewModal
        visible={reviewModalOpen}
        onClose={() => {
          setReviewModalOpen(false)
          setEditingReview(null)
        }}
        onSubmit={handleReviewSubmit}
        initialRating={editingReview ? editingReview.rating : 0}
        initialComment={editingReview?.comment ?? ''}
        initialIsAnonymous={editingReview?.is_anonymous ?? false}
        therapistName={fullName}
        isEdit={Boolean(editingReview)}
      />
    </>
  )
}

const styles = StyleSheet.create({
  flex: { flex: 1, backgroundColor: colors.bg },
  content: { padding: space.lg, gap: space.base, paddingBottom: space['4xl'] },
  pad: { padding: space.lg },
  hero: { flexDirection: 'row', gap: space.base, alignItems: 'flex-start' },
  heroText: { flex: 1, gap: space.sm },
  avatarClip: {
    width: 72,
    height: 72,
    borderRadius: 36,
    overflow: 'hidden',
    backgroundColor: colors.primarySubtle,
  },
  avatar: {
    width: 72,
    height: 72,
    borderRadius: 36,
    backgroundColor: colors.primarySubtle,
  },
  avatarPlaceholder: { alignItems: 'center', justifyContent: 'center' },
  initials: { fontSize: typography.xl, fontWeight: '800', color: colors.primary },
  name: { fontSize: typography['2xl'], fontWeight: '800', color: colors.ink },
  qualification: {
    fontSize: typography.sm,
    fontWeight: '700',
    color: colors.primary,
  },
  pwzfText: {
    fontSize: typography.xs,
    color: colors.muted,
  },
  bio: { fontSize: typography.base, color: colors.ink, lineHeight: 22 },
  actionRow: {
    marginTop: space.base,
    paddingTop: space.md,
    borderTopWidth: 1,
    borderTopColor: colors.border,
  },
  section: {
    fontSize: typography.sm,
    fontWeight: '700',
    color: colors.muted,
    textTransform: 'uppercase',
  },
  chipRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: space.sm,
    marginTop: space.sm,
  },
  chip: {
    paddingHorizontal: 10,
    paddingVertical: 5,
    borderRadius: radius.sm,
    borderWidth: 1,
    borderColor: colors.border,
    backgroundColor: colors.surfaceMuted,
    color: colors.muted,
    fontSize: typography.xs,
    fontWeight: '700',
    overflow: 'hidden',
  },
  chipOk: {
    borderColor: colors.primary,
    backgroundColor: colors.primarySubtle,
    color: colors.ink,
  },
  capRow: {
    marginTop: space.sm,
    paddingVertical: space.sm,
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: colors.border,
  },
  capHead: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    justifyContent: 'space-between',
    gap: space.sm,
  },
  capLabel: {
    flex: 1,
    fontSize: typography.base,
    fontWeight: '600',
    color: colors.ink,
    lineHeight: 22,
  },
  capToggle: {
    fontSize: typography.lg,
    color: colors.muted,
    fontWeight: '500',
    lineHeight: 22,
  },
  capDetail: {
    marginTop: space.sm,
    fontSize: typography.sm,
    color: colors.muted,
    lineHeight: 20,
  },
  course: { fontSize: typography.base, color: colors.ink },
  link: {
    fontSize: typography.base,
    color: colors.primary,
    fontWeight: '600',
    textDecorationLine: 'underline',
  },
  muted: { fontSize: typography.sm, color: colors.muted },
  ratingBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    marginTop: 2,
  },
  ratingStars: {
    fontSize: typography.base,
    color: colors.warning,
    fontWeight: '700',
  },
  ratingScore: {
    fontSize: typography.base,
    fontWeight: '700',
    color: colors.ink,
  },
  ratingCount: {
    fontSize: typography.sm,
    color: colors.muted,
  },
  noRatingText: {
    fontSize: typography.xs,
    color: colors.muted,
    fontStyle: 'italic',
  },
  reviewsTitleRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    gap: space.sm,
    marginBottom: space.sm,
    flexWrap: 'wrap',
  },
  reviewsTitleTextWrap: {
    flex: 1,
    minWidth: 160,
  },
  addReviewBtn: {
    paddingHorizontal: space.md,
    minHeight: 40,
  },
  breakdownCard: {
    backgroundColor: colors.surfaceMuted,
    borderRadius: radius.md,
    padding: space.md,
    gap: space.xs,
    marginTop: space.xs,
  },
  breakdownRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: space.sm,
  },
  breakdownStars: {
    width: 32,
    fontSize: typography.xs,
    fontWeight: '600',
    color: colors.muted,
  },
  barTrack: {
    flex: 1,
    height: 8,
    backgroundColor: colors.border,
    borderRadius: 4,
    overflow: 'hidden',
  },
  barFill: {
    height: '100%',
    backgroundColor: colors.warning,
    borderRadius: 4,
  },
  breakdownCount: {
    width: 24,
    fontSize: typography.xs,
    color: colors.muted,
    textAlign: 'right',
  },
  reviewList: {
    gap: space.md,
    marginTop: space.sm,
  },
  reviewCard: {
    backgroundColor: colors.surfaceMuted,
    borderRadius: radius.md,
    padding: space.md,
    gap: space.xs,
  },
  reviewCardHead: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    gap: space.sm,
  },
  reviewAuthorRow: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    gap: space.sm,
  },
  reviewAvatarAnon: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.border,
    alignItems: 'center',
    justifyContent: 'center',
  },
  reviewAvatarClip: {
    width: 36,
    height: 36,
    borderRadius: 18,
    overflow: 'hidden',
    borderWidth: 1,
    borderColor: colors.border,
  },
  reviewAvatarImg: {
    width: 36,
    height: 36,
  },
  reviewAvatarInitials: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: colors.primarySubtle,
    borderWidth: 1,
    borderColor: colors.border,
    alignItems: 'center',
    justifyContent: 'center',
  },
  reviewAvatarInitialsText: {
    fontSize: typography.xs,
    fontWeight: '700',
    color: colors.primary,
  },
  reviewAuthorCol: {
    flex: 1,
    gap: 2,
  },
  authorName: {
    fontSize: typography.base,
    fontWeight: '600',
    color: colors.ink,
  },
  verifiedBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  verifiedText: {
    fontSize: typography.xs,
    color: colors.primary,
    fontWeight: '600',
  },
  reviewScoreCol: {
    alignItems: 'flex-end',
    gap: 2,
  },
  reviewStars: {
    fontSize: typography.base,
    color: colors.warning,
    letterSpacing: 2,
  },
  reviewDate: {
    fontSize: typography.xs,
    color: colors.muted,
  },
  reviewComment: {
    fontSize: typography.sm,
    color: colors.ink,
    lineHeight: 20,
    marginTop: space.xs,
  },
  replyBox: {
    backgroundColor: colors.surface,
    borderLeftWidth: 3,
    borderLeftColor: colors.primary,
    padding: space.sm,
    borderRadius: radius.sm,
    gap: space.xs,
    marginTop: space.sm,
  },
  replyHeaderRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: space.sm,
  },
  replyAvatarWrap: {
    width: 30,
    height: 30,
    borderRadius: 15,
    overflow: 'hidden',
    backgroundColor: colors.primarySubtle,
    borderWidth: 1,
    borderColor: colors.border,
    alignItems: 'center',
    justifyContent: 'center',
  },
  replyAvatarImg: {
    width: 30,
    height: 30,
  },
  replyAvatarInitials: {
    width: 30,
    height: 30,
    borderRadius: 15,
    backgroundColor: colors.primarySubtle,
    alignItems: 'center',
    justifyContent: 'center',
  },
  replyAvatarInitialsText: {
    fontSize: 11,
    fontWeight: '700',
    color: colors.primary,
  },
  replyMetaCol: {
    flex: 1,
    gap: 1,
  },
  replyAuthorNameRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    flexWrap: 'wrap',
  },
  replyAuthorName: {
    fontSize: typography.xs,
    fontWeight: '700',
    color: colors.ink,
  },
  replyRoleBadge: {
    backgroundColor: colors.primarySubtle,
    paddingHorizontal: 5,
    paddingVertical: 1,
    borderRadius: 4,
  },
  replyRoleBadgeText: {
    fontSize: 9,
    fontWeight: '700',
    color: colors.primary,
    textTransform: 'uppercase',
  },
  replyDate: {
    fontSize: 10,
    color: colors.muted,
  },
  replyComment: {
    fontSize: typography.sm,
    color: colors.ink,
    lineHeight: 18,
    marginTop: 2,
  },
  reviewOwnActions: {
    flexDirection: 'row',
    gap: space.sm,
    marginTop: space.sm,
  },
  reviewSortRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: space.xs,
    marginTop: space.sm,
  },
  reviewSortLabel: {
    fontSize: typography.xs,
    color: colors.muted,
    fontWeight: '600',
    marginRight: 4,
  },
  sortChipsWrap: {
    flexDirection: 'row',
    gap: space.xs,
    alignItems: 'center',
  },
  sortChip: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    paddingVertical: 5,
    paddingHorizontal: space.sm,
    borderRadius: 999,
    borderWidth: 1,
    borderColor: colors.border,
    backgroundColor: colors.surface,
  },
  sortChipActive: {
    backgroundColor: colors.primary,
    borderColor: colors.primary,
  },
  sortChipText: {
    fontSize: typography.xs,
    fontWeight: '600',
    color: colors.muted,
  },
  sortChipTextActive: {
    color: colors.onPrimary,
  },
  breakdownRowSelected: {
    backgroundColor: colors.surface,
    borderRadius: radius.sm,
    paddingHorizontal: 4,
  },
  breakdownStarsSelected: {
    color: colors.primary,
    fontWeight: '700',
  },
  breakdownCountSelected: {
    color: colors.primary,
    fontWeight: '700',
  },
  activeFilterRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    backgroundColor: colors.surface,
    paddingVertical: space.xs,
    paddingHorizontal: space.sm,
    borderRadius: radius.sm,
    marginTop: space.xs,
    borderWidth: 1,
    borderColor: colors.border,
  },
  activeFilterText: {
    fontSize: typography.xs,
    color: colors.ink,
  },
  bold: {
    fontWeight: '700',
  },
  clearFilterBtn: {
    paddingVertical: space.xs,
    paddingHorizontal: space.sm,
    minHeight: 36,
    justifyContent: 'center',
  },
  clearFilterText: {
    fontSize: typography.xs,
    color: colors.primary,
    fontWeight: '600',
  },
  nameAndBadgeWrap: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: space.xs,
    flexWrap: 'wrap',
  },
  ownReviewBadge: {
    backgroundColor: colors.primary,
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 4,
  },
  ownReviewText: {
    color: colors.onPrimary,
    fontSize: typography.xs,
    fontWeight: '700',
  },
  reviewCardOwn: {
    borderColor: colors.primary,
    borderWidth: 1.5,
  },
  emptyFilteredReviews: {
    paddingVertical: space.md,
    alignItems: 'center',
  },
  expandReviewsBtn: {
    marginTop: space.xs,
  },
})
