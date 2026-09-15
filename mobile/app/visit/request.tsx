import { Stack, useLocalSearchParams, useRouter } from 'expo-router'
import { useEffect, useMemo, useState } from 'react'
import { Pressable, StyleSheet, Text, View } from 'react-native'
import { Ionicons } from '@expo/vector-icons'

import { api, getErrorMessage } from '@/api/client'
import { patientApi } from '@/api/patient'
import type { TherapyType } from '@/api/types'
import { ErrorBanner, LoadingBlock } from '@/components/AsyncState'
import { Button } from '@/components/Button'
import { DateTimePickerField } from '@/components/DateTimePickerField'
import { Field } from '@/components/Field'
import { KeyboardAwareForm } from '@/components/KeyboardAwareForm'
import { SectionCard } from '@/components/ScreenHeader'
import { useToast } from '@/components/ToastContext'
import { addMinutesISO } from '@/lib/format'
import { colors, radius, space, typography } from '@/theme/tokens'

interface Therapist {
  id: string
  first_name: string
  last_name: string
  qualification_label?: string
  location_address?: string
}

function defaultStart(): Date {
  const date = new Date()
  date.setDate(date.getDate() + 1)
  date.setHours(10, 0, 0, 0)
  return date
}

export default function VisitRequestScreen() {
  const router = useRouter()
  const { toast } = useToast()
  const { therapist_id: initialTherapistId } = useLocalSearchParams<{ therapist_id?: string }>()

  const [therapists, setTherapists] = useState<Therapist[]>([])
  const [selectedTherapistId, setSelectedTherapistId] = useState<string>(initialTherapistId || '')
  const [types, setTypes] = useState<TherapyType[]>([])
  const [loading, setLoading] = useState(true)
  const [typesLoading, setTypesLoading] = useState(false)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [therapyTypeId, setTherapyTypeId] = useState('')
  const [startAt, setStartAt] = useState(defaultStart)
  const [note, setNote] = useState('')

  const selectedType = useMemo(
    () => types.find((item) => item.id === therapyTypeId) ?? null,
    [types, therapyTypeId],
  )

  const selectedTherapist = useMemo(
    () => therapists.find((t) => t.id === selectedTherapistId) ?? null,
    [therapists, selectedTherapistId],
  )

  const minimumDate = useMemo(() => {
    const now = new Date()
    return new Date(now.getFullYear(), now.getMonth(), now.getDate())
  }, [])

  // Load therapists list and initial therapy types
  useEffect(() => {
    let cancelled = false
    async function init() {
      setLoading(true)
      setError(null)
      try {
        const res = await api.get<Therapist[] | { results: Therapist[] }>('/me/therapists/')
        const myTherapists = Array.isArray(res) ? res : res.results || []
        if (cancelled) return

        setTherapists(myTherapists)

        const activeId =
          initialTherapistId && myTherapists.some((t) => t.id === initialTherapistId)
            ? initialTherapistId
            : myTherapists[0]?.id || ''

        setSelectedTherapistId(activeId)

        if (activeId) {
          const typeData = await patientApi.getTherapyTypes(activeId)
          if (!cancelled) {
            setTypes(typeData)
            setTherapyTypeId(typeData[0]?.id || '')
          }
        }
      } catch (err) {
        if (!cancelled) {
          const msg = getErrorMessage(err, 'Nie udało się pobrać danych do umawiania wizyty.')
          setError(msg)
          toast.error('Błąd pobierania', msg)
        }
      } finally {
        if (!cancelled) {
          setLoading(false)
        }
      }
    }
    void init()
    return () => {
      cancelled = true
    }
  }, [initialTherapistId])

  // Handle changing therapist
  const handleSelectTherapist = async (therapistId: string) => {
    if (therapistId === selectedTherapistId) return
    setSelectedTherapistId(therapistId)
    setTypesLoading(true)
    setError(null)
    try {
      const typeData = await patientApi.getTherapyTypes(therapistId)
      setTypes(typeData)
      setTherapyTypeId(typeData[0]?.id || '')
    } catch (err) {
      const msg = getErrorMessage(err, 'Nie udało się pobrać usług tego fizjoterapeuty.')
      setError(msg)
      toast.error('Błąd pobierania', msg)
    } finally {
      setTypesLoading(false)
    }
  }

  async function onSubmit() {
    if (!selectedTherapistId) {
      const msg = 'Wybierz fizjoterapeutę.'
      setError(msg)
      toast.error('Błąd wyboru', msg)
      return
    }
    if (!selectedType) {
      const msg = 'Wybierz typ wizyty.'
      setError(msg)
      toast.error('Błąd wyboru', msg)
      return
    }
    if (startAt.getTime() <= Date.now()) {
      const msg = 'Wybierz termin wizyty w przyszłości.'
      toast.error('Nieprawidłowa data', msg)
      return
    }

    setBusy(true)
    try {
      const startIso = startAt.toISOString()
      const endIso = addMinutesISO(startIso, selectedType.duration_min)
      const visit = await patientApi.requestVisit({
        therapist_id: selectedTherapistId,
        therapy_type_id: selectedType.id,
        start_at: startIso,
        end_at: endIso,
        patient_note: note.trim(),
      })
      toast.success('Wysłano zgłoszenie', 'Fizjoterapeuta otrzymał Twoją prośbę o wizytę.')
      router.replace(`/visit/${visit.id}`)
    } catch (err) {
      const errMsg = getErrorMessage(err, 'Nie udało się wysłać zgłoszenia.')
      let title = 'Brak możliwości rezerwacji'
      if (errMsg.includes('zarezerwowana') || errMsg.includes('zajęt')) {
        title = 'Godzina zajęta'
      } else if (errMsg.includes('godzinach przyjęć') || errMsg.includes('grafik')) {
        title = 'Poza godzinami pracy'
      } else if (errMsg.includes('wolnym od pracy') || errMsg.includes('święto')) {
        title = 'Dzień wolny'
      }
      toast.error(title, errMsg)
    } finally {
      setBusy(false)
    }
  }

  return (
    <>
      <Stack.Screen options={{ title: 'Umów wizytę', headerShown: true }} />
      {loading ? (
        <LoadingBlock label="Ładowanie formularza wizyty…" />
      ) : (
        <KeyboardAwareForm style={styles.flex} contentContainerStyle={styles.content}>
          <Text style={styles.lead}>
            Wybierz specjalistę, rodzaj usługi i proponowany termin. Fizjoterapeuta potwiedzi lub
            zaproponuje inny czas.
          </Text>

          {error ? <ErrorBanner message={error} /> : null}

          {/* Section: Select Therapist */}
          {therapists.length === 0 ? (
            <SectionCard style={styles.warningCard}>
              <Ionicons name="alert-circle-outline" size={32} color={colors.warning} />
              <Text style={styles.warningTitle}>Brak przypisanych fizjoterapeutów</Text>
              <Text style={styles.mutedCentered}>
                Aby umówić wizytę, musisz mieć na swojej liście co najmniej jednego specjalistę.
              </Text>
              <Button
                title="Wyszukaj specjalistę"
                onPress={() => router.push('/(tabs)/therapists')}
              />
            </SectionCard>
          ) : (
            <SectionCard>
              <Text style={styles.label}>Wybierz specjalistę</Text>
              <View style={styles.therapistSelectorList}>
                {therapists.map((t) => {
                  const selected = t.id === selectedTherapistId
                  return (
                    <Pressable
                      key={t.id}
                      onPress={() => void handleSelectTherapist(t.id)}
                      style={[styles.therapistTile, selected ? styles.therapistTileOn : null]}
                      accessibilityRole="radio"
                      accessibilityState={{ selected }}
                    >
                      <View style={styles.therapistAvatar}>
                        <Text style={styles.avatarInitials}>
                          {(t.first_name?.[0] ?? '') + (t.last_name?.[0] ?? '')}
                        </Text>
                      </View>
                      <View style={styles.therapistTileInfo}>
                        <Text style={styles.therapistTileName}>
                          {t.first_name} {t.last_name}
                        </Text>
                        {t.qualification_label ? (
                          <Text style={styles.therapistTileMeta}>{t.qualification_label}</Text>
                        ) : null}
                      </View>
                      <Ionicons
                        name={selected ? 'checkmark-circle' : 'ellipse-outline'}
                        size={22}
                        color={selected ? colors.primary : colors.muted}
                      />
                    </Pressable>
                  )
                })}
              </View>
            </SectionCard>
          )}

          {/* Section: Therapy Types */}
          {selectedTherapistId ? (
            typesLoading ? (
              <LoadingBlock label="Pobieranie usług..." />
            ) : types.length === 0 ? (
              <SectionCard>
                <Text style={styles.muted}>
                  Brak dostępnych typów wizyt w cenniku wybranego fizjoterapeuty.
                </Text>
              </SectionCard>
            ) : (
              <SectionCard>
                <Text style={styles.label}>
                  Usługa (
                  {selectedTherapist
                    ? `${selectedTherapist.first_name} ${selectedTherapist.last_name}`
                    : ''}
                  )
                </Text>
                <View style={styles.typeList} accessibilityRole="radiogroup">
                  {types.map((type) => {
                    const selected = type.id === therapyTypeId
                    return (
                      <Pressable
                        key={type.id}
                        onPress={() => setTherapyTypeId(type.id)}
                        style={[styles.typeTile, selected ? styles.typeTileOn : null]}
                        accessibilityRole="radio"
                        accessibilityState={{ selected }}
                      >
                        <View
                          style={[
                            styles.typeDot,
                            { backgroundColor: type.color_hex || colors.primary },
                          ]}
                        />
                        <View style={styles.typeBody}>
                          <Text style={styles.typeName}>{type.name}</Text>
                          <Text style={styles.typeMeta}>{type.duration_min} min</Text>
                        </View>
                        {selected ? (
                          <Ionicons name="checkmark" size={18} color={colors.primary} />
                        ) : null}
                      </Pressable>
                    )
                  })}
                </View>
              </SectionCard>
            )
          ) : null}

          {/* Section: Date & Time Picker */}
          {selectedTherapistId && types.length > 0 ? (
            <>
              <SectionCard>
                <DateTimePickerField
                  label="Proponowany termin"
                  value={startAt}
                  onChange={setStartAt}
                  minimumDate={minimumDate}
                  hint={
                    selectedType
                      ? `Koniec wyliczymy automatycznie (${selectedType.duration_min} min).`
                      : undefined
                  }
                />
              </SectionCard>

              <SectionCard>
                <Field
                  label="Notatka dla terapeuty (opcjonalnie)"
                  value={note}
                  onChangeText={setNote}
                  maxLength={5000}
                  multiline
                  style={styles.note}
                  hint="Np. preferowana pora, opis dolegliwości, przebyty uraz."
                />
              </SectionCard>

              <Button
                title="Wyślij zgłoszenie"
                loading={busy}
                disabled={!therapyTypeId || types.length === 0}
                onPress={() => void onSubmit()}
              />
            </>
          ) : null}

          <Button title="Anuluj" variant="ghost" onPress={() => router.back()} disabled={busy} />
        </KeyboardAwareForm>
      )}
    </>
  )
}

const styles = StyleSheet.create({
  flex: { flex: 1, backgroundColor: colors.bg },
  content: { padding: space.base, gap: space.base, paddingBottom: space['4xl'] },
  lead: { fontSize: typography.sm, color: colors.muted, lineHeight: 20 },
  label: {
    fontSize: typography.base,
    fontWeight: '700',
    color: colors.ink,
    marginBottom: space.xs,
  },
  muted: { fontSize: typography.sm, color: colors.muted },
  mutedCentered: { fontSize: typography.sm, color: colors.muted, textAlign: 'center' },
  warningCard: { alignItems: 'center', gap: space.sm, paddingVertical: space.lg },
  warningTitle: { fontSize: typography.lg, fontWeight: '700', color: colors.ink },
  therapistSelectorList: { gap: space.xs },
  therapistTile: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: space.md,
    padding: space.md,
    borderRadius: radius.md,
    borderWidth: 1,
    borderColor: colors.border,
    backgroundColor: colors.surface,
  },
  therapistTileOn: {
    borderColor: colors.primary,
    backgroundColor: colors.primarySubtle,
  },
  therapistAvatar: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: colors.primarySubtle,
    alignItems: 'center',
    justifyContent: 'center',
  },
  avatarInitials: {
    fontSize: typography.sm,
    fontWeight: '700',
    color: colors.primary,
  },
  therapistTileInfo: { flex: 1, gap: 2 },
  therapistTileName: { fontSize: typography.base, fontWeight: '700', color: colors.ink },
  therapistTileMeta: { fontSize: typography.xs, color: colors.primary, fontWeight: '600' },
  typeList: { gap: space.sm },
  typeTile: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: space.md,
    minHeight: 52,
    paddingHorizontal: space.base,
    paddingVertical: space.md,
    borderRadius: radius.md,
    borderWidth: 1,
    borderColor: colors.border,
    backgroundColor: colors.surface,
  },
  typeTileOn: {
    borderColor: colors.primary,
    backgroundColor: colors.surfaceMuted,
  },
  typeDot: {
    width: 12,
    height: 12,
    borderRadius: 6,
  },
  typeBody: { flex: 1, gap: 2 },
  typeName: { fontSize: typography.base, fontWeight: '700', color: colors.ink },
  typeMeta: { fontSize: typography.sm, color: colors.muted },
  note: { minHeight: 96, textAlignVertical: 'top' },
})
