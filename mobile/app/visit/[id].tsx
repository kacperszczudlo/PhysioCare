/**
 * @file [id].tsx
 * @description Ekran szczegółów wizyty (lokalizacja na mapie, notatki, możliwość przełożenia lub odwołania).
 */

import { Stack, useLocalSearchParams, useRouter } from 'expo-router'
import { useCallback, useEffect, useMemo, useState } from 'react'
import { Alert, Modal, StyleSheet, Text, View } from 'react-native'

import { getErrorMessage } from '@/api/client'
import { patientApi } from '@/api/patient'
import type { Visit } from '@/api/types'
import { ErrorBanner, LoadingBlock } from '@/components/AsyncState'
import { MobileVisitDetailSkeleton } from '@/components/skeletons/MobileSkeletons'
import { Button } from '@/components/Button'
import { DateTimePickerField } from '@/components/DateTimePickerField'
import { Field } from '@/components/Field'
import { KeyboardAwareForm } from '@/components/KeyboardAwareForm'
import { SectionCard } from '@/components/ScreenHeader'
import { LocationMapCard } from '@/components/LocationMapCard'
import { useToast } from '@/components/ToastContext'
import { addMinutesISO, formatDateTime, formatTimeRange } from '@/lib/format'
import { VisitStatusBadge } from '@/components/VisitStatusBadge'
import { ReviewModal } from '@/components/ReviewModal'
import { colors, radius, space, typography } from '@/theme/tokens'

function defaultRescheduleStart(from?: string): Date {
  if (from) {
    const parsed = new Date(from)
    if (!Number.isNaN(parsed.getTime())) {
      return parsed
    }
  }
  const date = new Date()
  date.setDate(date.getDate() + 1)
  date.setHours(10, 0, 0, 0)
  return date
}

/**
 * Ekran prezentujący szczegóły pojedynczej wizyty z opcją zmiany terminu lub odwołania.
 *
 * @returns Element React Native prezentujący widok wizyty.
 */
export default function VisitDetailScreen() {
  const { id } = useLocalSearchParams<{ id: string }>()
  const router = useRouter()
  const { toast } = useToast()
  const [visit, setVisit] = useState<Visit | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)
  const [rescheduleOpen, setRescheduleOpen] = useState(false)
  const [newStart, setNewStart] = useState(() => defaultRescheduleStart())
  const [cancelReason, setCancelReason] = useState('')
  const [reviewModalOpen, setReviewModalOpen] = useState(false)
  const [isEditingReview, setIsEditingReview] = useState(false)

  const minimumDate = useMemo(() => {
    const now = new Date()
    return new Date(now.getFullYear(), now.getMonth(), now.getDate())
  }, [])

  const load = useCallback(async () => {
    if (!id) {
      return
    }
    setError(null)
    setLoading(true)
    try {
      const data = await patientApi.getVisit(id)
      setVisit(data)
      setNewStart(defaultRescheduleStart(data.start_at))
    } catch (err) {
      setError(getErrorMessage(err, 'Nie udało się pobrać wizyty.'))
    } finally {
      setLoading(false)
    }
  }, [id])

  useEffect(() => {
    void load()
  }, [load])

  async function onReschedule() {
    if (!visit) {
      return
    }
    if (newStart.getTime() <= Date.now()) {
      toast.error('Nieprawidłowa data', 'Termin musi być w przyszłości.')
      return
    }
    setBusy(true)
    try {
      const startIso = newStart.toISOString()
      const endIso = addMinutesISO(startIso, visit.therapy_type_duration_min || 45)
      const updated = await patientApi.rescheduleVisit(visit.id, {
        start_at: startIso,
        end_at: endIso,
      })
      setVisit(updated)
      setRescheduleOpen(false)
      toast.success('Termin wizyty został zmieniony.')
    } catch (err) {
      const msg = getErrorMessage(err, 'Nie udało się zmienić terminu.')
      let title = 'Błąd zmiany terminu'
      if (msg.includes('zarezerwowana') || msg.includes('zajęt')) {
        title = 'Godzina zajęta'
      } else if (msg.includes('godzinach przyjęć')) {
        title = 'Poza godzinami pracy'
      } else if (msg.includes('wolnym od pracy') || msg.includes('święto')) {
        title = 'Dzień wolny'
      }
      toast.error(title, msg)
    } finally {
      setBusy(false)
    }
  }

  function confirmCancel() {
    const pending = visit?.status === 'PENDING_APPROVAL'
    Alert.alert(
      pending ? 'Wycofać zgłoszenie?' : 'Odwołać wizytę?',
      'Tej operacji nie można cofnąć z poziomu aplikacji.',
      [
        { text: 'Anuluj', style: 'cancel' },
        {
          text: pending ? 'Wycofaj' : 'Odwołaj',
          style: 'destructive',
          onPress: () => {
            void (async () => {
              if (!visit) {
                return
              }
              setBusy(true)
              try {
                const updated = await patientApi.cancelVisit(visit.id, cancelReason.trim())
                setVisit(updated)
                toast.warning(pending ? 'Zgłoszenie zostało wycofane.' : 'Wizyta została odwołana.')
              } catch (err) {
                const msg = getErrorMessage(
                  err,
                  pending ? 'Nie udało się wycofać zgłoszenia.' : 'Nie udało się odwołać wizyty.',
                )
                toast.error(msg)
              } finally {
                setBusy(false)
              }
            })()
          },
        },
      ],
    )
  }

  if (loading) {
    return <LoadingBlock skeleton={<MobileVisitDetailSkeleton />} />
  }

  if (!visit) {
    return (
      <View style={styles.pad}>
        <ErrorBanner message={error ?? 'Wizyta nie istnieje.'} onRetry={() => void load()} />
      </View>
    )
  }

  const isCompleted = visit.status === 'COMPLETED'
  const isPending = visit.status === 'PENDING_APPROVAL'
  const canManage = visit.status === 'SCHEDULED' || isPending

  async function handleReviewSubmit(data: { rating: number; comment: string; is_anonymous: boolean }) {
    if (!visit) return
    if (visit.review?.id) {
      await patientApi.editReview(visit.review.id, data)
      toast.success('Zaktualizowano opinię', 'Twoja opinia została pomyślnie zmieniona.')
    } else {
      await patientApi.createVisitReview(visit.id, data)
      toast.success('Dziękujemy za opinię!', 'Twoja ocena została opublikowana.')
    }
    void load()
  }

  async function handleDeleteReview() {
    if (!visit?.review?.id) return
    Alert.alert('Usunąć opinię?', 'Czy na pewno chcesz usunąć swoją opinię dla tej wizyty?', [
      { text: 'Anuluj', style: 'cancel' },
      {
        text: 'Usuń',
        style: 'destructive',
        onPress: async () => {
          try {
            await patientApi.deleteReview(visit.review!.id)
            toast.success('Opinia usunięta')
            void load()
          } catch (err) {
            toast.error('Błąd usuwania', getErrorMessage(err, 'Nie udało się usunąć opinii.'))
          }
        },
      },
    ])
  }

  return (
    <>
      <Stack.Screen options={{ title: visit.therapy_type_name }} />
      <KeyboardAwareForm style={styles.flex} contentContainerStyle={styles.content}>
        {error ? <ErrorBanner message={error} onRetry={() => void load()} /> : null}

        <SectionCard>
          <View style={styles.headerRow}>
            <Text style={styles.title}>{visit.therapy_type_name}</Text>
            <VisitStatusBadge status={visit.status} />
          </View>
          {isPending ? (
            <Text style={styles.muted}>
              Zgłoszenie czeka na zatwierdzenie przez terapeutę. Możesz zmienić termin albo je
              wycofać.
            </Text>
          ) : null}
          <Text style={styles.body}>{formatDateTime(visit.start_at)}</Text>
          <Text style={styles.muted}>{formatTimeRange(visit.start_at, visit.end_at)}</Text>
        </SectionCard>

        {isCompleted ? (
          <SectionCard>
            <Text style={styles.section}>Twoja opinia o wizycie</Text>
            {visit.review ? (
              <View style={styles.reviewBox}>
                <View style={styles.reviewHeader}>
                  <Text style={styles.reviewStars}>
                    {'★'.repeat(visit.review.rating)}{'☆'.repeat(5 - visit.review.rating)}
                  </Text>
                  <Text style={styles.reviewDate}>
                    {visit.review.created_at ? formatDateTime(visit.review.created_at) : ''}
                  </Text>
                </View>
                {visit.review.comment ? (
                  <Text style={styles.reviewComment}>{visit.review.comment}</Text>
                ) : null}
                {visit.review.therapist_reply ? (
                  <View style={styles.replyBox}>
                    <Text style={styles.replyTitle}>Odpowiedź terapeuty:</Text>
                    <Text style={styles.replyComment}>{visit.review.therapist_reply}</Text>
                  </View>
                ) : null}
                <View style={styles.reviewActions}>
                  <Button
                    title="Edytuj opinię"
                    variant="secondary"
                    onPress={() => {
                      setIsEditingReview(true)
                      setReviewModalOpen(true)
                    }}
                  />
                  <Button
                    title="Usuń"
                    variant="danger"
                    onPress={handleDeleteReview}
                  />
                </View>
              </View>
            ) : (
              <View style={styles.reviewPrompt}>
                <Text style={styles.muted}>
                  Wizyta dobiegła końca. Podziel się swoją opinią o przebiegu terapii i specjaliście!
                </Text>
                <Button
                  title="★ Oceń tę wizytę"
                  variant="primary"
                  onPress={() => {
                    setIsEditingReview(false)
                    setReviewModalOpen(true)
                  }}
                />
              </View>
            )}
          </SectionCard>
        ) : null}

        <SectionCard>
          <Text style={styles.section}>Terapeuta</Text>
          <Text style={styles.body}>
            {visit.therapist_first_name} {visit.therapist_last_name}
          </Text>
          <Button
            title="Zobacz profil"
            variant="secondary"
            onPress={() => router.push(`/therapist/${visit.therapist}`)}
          />
        </SectionCard>

        <SectionCard>
          <LocationMapCard address={visit.location_address || ''} title="Lokalizacja wizyty" />
          {visit.patient_note ? (
            <>
              <Text style={styles.section}>Twoja notatka</Text>
              <Text style={styles.body}>{visit.patient_note}</Text>
            </>
          ) : null}
          <Text style={styles.section}>Przygotowanie</Text>
          <Text style={styles.body}>{visit.prep_instructions || 'Brak instrukcji.'}</Text>
          {visit.patient_summary ? (
            <>
              <Text style={styles.section}>Podsumowanie po wizycie</Text>
              <Text style={styles.body}>{visit.patient_summary}</Text>
            </>
          ) : null}
          {visit.cancel_reason ? (
            <>
              <Text style={styles.section}>Powód odwołania</Text>
              <Text style={styles.body}>{visit.cancel_reason}</Text>
            </>
          ) : null}
        </SectionCard>

        {canManage ? (
          <SectionCard>
            <Button
              title={isPending ? 'Zmień proponowany termin' : 'Zmień termin'}
              onPress={() => setRescheduleOpen(true)}
            />
            <Field
              label={isPending ? 'Powód wycofania (opcjonalnie)' : 'Powód odwołania (opcjonalnie)'}
              value={cancelReason}
              onChangeText={setCancelReason}
            />
            <Button
              title={isPending ? 'Wycofaj zgłoszenie' : 'Odwołaj wizytę'}
              variant="danger"
              loading={busy}
              onPress={confirmCancel}
            />
          </SectionCard>
        ) : null}
      </KeyboardAwareForm>

      <ReviewModal
        visible={reviewModalOpen}
        onClose={() => setReviewModalOpen(false)}
        onSubmit={handleReviewSubmit}
        initialRating={isEditingReview ? (visit.review?.rating ?? 0) : 0}
        initialComment={visit.review?.comment ?? ''}
        initialIsAnonymous={visit.review?.is_anonymous ?? false}
        therapistName={`${visit.therapist_first_name} ${visit.therapist_last_name}`}
        isEdit={isEditingReview}
      />

      <Modal visible={rescheduleOpen} animationType="slide" transparent>
        <View style={styles.modalBackdrop}>
          <KeyboardAwareForm style={styles.modalScroll} contentContainerStyle={styles.modalCard}>
            <Text style={styles.title}>Nowy termin</Text>
            <Text style={styles.muted}>
              Wybierz dzień i godzinę. Koniec wyliczymy z czasu zabiegu (
              {visit.therapy_type_duration_min || 45} min).
            </Text>
            <DateTimePickerField
              label="Termin wizyty"
              value={newStart}
              onChange={setNewStart}
              minimumDate={minimumDate}
            />
            <Button title="Zapisz termin" loading={busy} onPress={() => void onReschedule()} />
            <Button title="Anuluj" variant="ghost" onPress={() => setRescheduleOpen(false)} />
          </KeyboardAwareForm>
        </View>
      </Modal>
    </>
  )
}

const styles = StyleSheet.create({
  flex: { flex: 1, backgroundColor: colors.bg },
  content: { padding: space.lg, gap: space.base, paddingBottom: space['4xl'] },
  pad: { padding: space.lg },
  title: { flex: 1, fontSize: typography.xl, fontWeight: '700', color: colors.ink },
  headerRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    gap: space.sm,
  },
  section: {
    fontSize: typography.sm,
    fontWeight: '700',
    color: colors.muted,
    textTransform: 'uppercase',
  },
  body: { fontSize: typography.base, color: colors.ink },
  link: {
    fontSize: typography.base,
    color: colors.primary,
    fontWeight: '600',
    textDecorationLine: 'underline',
  },
  meta: { fontSize: typography.sm, color: colors.primary, fontWeight: '700' },
  muted: { fontSize: typography.sm, color: colors.muted },
  modalBackdrop: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.35)',
    justifyContent: 'flex-end',
  },
  modalScroll: {
    maxHeight: '92%',
  },
  modalCard: {
    backgroundColor: colors.surface,
    borderTopLeftRadius: 16,
    borderTopRightRadius: 16,
    padding: space.lg,
    gap: space.md,
    paddingBottom: space['3xl'],
  },
  reviewBox: {
    backgroundColor: colors.surfaceMuted,
    borderRadius: radius.md,
    padding: space.md,
    gap: space.sm,
  },
  reviewHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  reviewStars: {
    fontSize: typography.lg,
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
  },
  replyBox: {
    backgroundColor: colors.surface,
    borderLeftWidth: 3,
    borderLeftColor: colors.primary,
    padding: space.sm,
    borderRadius: radius.sm,
    gap: 2,
    marginTop: space.xs,
  },
  replyTitle: {
    fontSize: typography.xs,
    fontWeight: '700',
    color: colors.primary,
  },
  replyComment: {
    fontSize: typography.xs,
    color: colors.ink,
  },
  reviewActions: {
    flexDirection: 'row',
    gap: space.sm,
    marginTop: space.xs,
  },
  reviewPrompt: {
    gap: space.md,
    paddingVertical: space.xs,
  },
})
