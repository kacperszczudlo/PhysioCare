import { Stack, useLocalSearchParams, useRouter } from 'expo-router'
import { useCallback, useEffect, useState } from 'react'
import { Alert, Modal, Pressable, ScrollView, StyleSheet, Text, View } from 'react-native'

import { getErrorMessage } from '@/api/client'
import { patientApi } from '@/api/patient'
import type { Visit } from '@/api/types'
import { ErrorBanner, LoadingBlock } from '@/components/AsyncState'
import { Button } from '@/components/Button'
import { Field } from '@/components/Field'
import { SectionCard } from '@/components/ScreenHeader'
import { addMinutesISO, formatDateTime, formatTimeRange, visitStatusLabel } from '@/lib/format'
import { openAddressInMaps } from '@/lib/maps'
import { colors, space, typography } from '@/theme/tokens'

export default function VisitDetailScreen() {
  const { id } = useLocalSearchParams<{ id: string }>()
  const router = useRouter()
  const [visit, setVisit] = useState<Visit | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)
  const [rescheduleOpen, setRescheduleOpen] = useState(false)
  const [newStart, setNewStart] = useState('')
  const [cancelReason, setCancelReason] = useState('')

  const load = useCallback(async () => {
    if (!id) {
      return
    }
    setError(null)
    setLoading(true)
    try {
      const data = await patientApi.getVisit(id)
      setVisit(data)
      setNewStart(data.start_at.slice(0, 16))
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
    if (!visit || !newStart) {
      return
    }
    setBusy(true)
    setError(null)
    try {
      const startIso = new Date(newStart).toISOString()
      const endIso = addMinutesISO(startIso, visit.therapy_type_duration_min || 45)
      const updated = await patientApi.rescheduleVisit(visit.id, {
        start_at: startIso,
        end_at: endIso,
      })
      setVisit(updated)
      setRescheduleOpen(false)
    } catch (err) {
      setError(getErrorMessage(err, 'Nie udało się zmienić terminu.'))
    } finally {
      setBusy(false)
    }
  }

  function confirmCancel() {
    Alert.alert('Odwołać wizytę?', 'Tej operacji nie można cofnąć z poziomu aplikacji.', [
      { text: 'Anuluj', style: 'cancel' },
      {
        text: 'Odwołaj',
        style: 'destructive',
        onPress: () => {
          void (async () => {
            if (!visit) {
              return
            }
            setBusy(true)
            setError(null)
            try {
              const updated = await patientApi.cancelVisit(visit.id, cancelReason.trim())
              setVisit(updated)
            } catch (err) {
              setError(getErrorMessage(err, 'Nie udało się odwołać wizyty.'))
            } finally {
              setBusy(false)
            }
          })()
        },
      },
    ])
  }

  if (loading) {
    return <LoadingBlock />
  }

  if (!visit) {
    return (
      <View style={styles.pad}>
        <ErrorBanner message={error ?? 'Wizyta nie istnieje.'} onRetry={() => void load()} />
      </View>
    )
  }

  const canManage = visit.status === 'SCHEDULED'

  return (
    <>
      <Stack.Screen options={{ title: visit.therapy_type_name }} />
      <ScrollView style={styles.flex} contentContainerStyle={styles.content}>
        {error ? <ErrorBanner message={error} onRetry={() => void load()} /> : null}

        <SectionCard>
          <Text style={styles.title}>{visit.therapy_type_name}</Text>
          <Text style={styles.meta}>{visitStatusLabel(visit.status)}</Text>
          <Text style={styles.body}>{formatDateTime(visit.start_at)}</Text>
          <Text style={styles.muted}>{formatTimeRange(visit.start_at, visit.end_at)}</Text>
        </SectionCard>

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
          <Text style={styles.section}>Lokalizacja</Text>
          {visit.location_address ? (
            <Pressable
              onPress={() => openAddressInMaps(visit.location_address)}
              accessibilityRole="link"
              accessibilityHint="Otwiera adres w Google Maps"
            >
              <Text style={styles.link}>{visit.location_address}</Text>
              <Text style={styles.muted}>Otwórz w Google Maps</Text>
            </Pressable>
          ) : (
            <Text style={styles.body}>—</Text>
          )}
          <Text style={styles.section}>Przygotowanie</Text>
          <Text style={styles.body}>{visit.prep_instructions || 'Brak instrukcji.'}</Text>
          {visit.cancel_reason ? (
            <>
              <Text style={styles.section}>Powód odwołania</Text>
              <Text style={styles.body}>{visit.cancel_reason}</Text>
            </>
          ) : null}
        </SectionCard>

        {canManage ? (
          <SectionCard>
            <Button title="Zmień termin" onPress={() => setRescheduleOpen(true)} />
            <Field
              label="Powód odwołania (opcjonalnie)"
              value={cancelReason}
              onChangeText={setCancelReason}
            />
            <Button
              title="Odwołaj wizytę"
              variant="danger"
              loading={busy}
              onPress={confirmCancel}
            />
          </SectionCard>
        ) : null}
      </ScrollView>

      <Modal visible={rescheduleOpen} animationType="slide" transparent>
        <View style={styles.modalBackdrop}>
          <View style={styles.modalCard}>
            <Text style={styles.title}>Nowy termin</Text>
            <Text style={styles.muted}>
              Podaj datę i godzinę (lokalna). Koniec wyliczymy z czasu zabiegu.
            </Text>
            <Field
              label="Start (YYYY-MM-DDTHH:mm)"
              value={newStart}
              onChangeText={setNewStart}
              autoCapitalize="none"
              hint="Np. 2026-06-12T11:00"
            />
            <Button title="Zapisz termin" loading={busy} onPress={() => void onReschedule()} />
            <Button title="Anuluj" variant="ghost" onPress={() => setRescheduleOpen(false)} />
          </View>
        </View>
      </Modal>
    </>
  )
}

const styles = StyleSheet.create({
  flex: { flex: 1, backgroundColor: colors.bg },
  content: { padding: space.lg, gap: space.base, paddingBottom: space['4xl'] },
  pad: { padding: space.lg },
  title: { fontSize: typography.xl, fontWeight: '700', color: colors.ink },
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
  modalCard: {
    backgroundColor: colors.surface,
    borderTopLeftRadius: 16,
    borderTopRightRadius: 16,
    padding: space.lg,
    gap: space.md,
  },
})
