import { Stack, useRouter } from 'expo-router'
import { useEffect, useMemo, useState } from 'react'
import {
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from 'react-native'

import { getErrorMessage } from '@/api/client'
import { patientApi } from '@/api/patient'
import type { TherapyType } from '@/api/types'
import { ErrorBanner, LoadingBlock } from '@/components/AsyncState'
import { Button } from '@/components/Button'
import { Field } from '@/components/Field'
import { addMinutesISO } from '@/lib/format'
import { colors, radius, space, typography } from '@/theme/tokens'

function defaultStartLocal(): string {
  const date = new Date()
  date.setDate(date.getDate() + 1)
  date.setHours(10, 0, 0, 0)
  const y = date.getFullYear()
  const m = String(date.getMonth() + 1).padStart(2, '0')
  const d = String(date.getDate()).padStart(2, '0')
  const hh = String(date.getHours()).padStart(2, '0')
  const mm = String(date.getMinutes()).padStart(2, '0')
  return `${y}-${m}-${d}T${hh}:${mm}`
}

export default function VisitRequestScreen() {
  const router = useRouter()
  const [types, setTypes] = useState<TherapyType[]>([])
  const [loading, setLoading] = useState(true)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [therapyTypeId, setTherapyTypeId] = useState('')
  const [startLocal, setStartLocal] = useState(defaultStartLocal)
  const [note, setNote] = useState('')

  const selectedType = useMemo(
    () => types.find((item) => item.id === therapyTypeId) ?? null,
    [types, therapyTypeId],
  )

  useEffect(() => {
    let cancelled = false
    async function load() {
      setLoading(true)
      setError(null)
      try {
        const data = await patientApi.getTherapyTypes()
        if (cancelled) {
          return
        }
        setTypes(data)
        setTherapyTypeId(data[0]?.id || '')
      } catch (err) {
        if (!cancelled) {
          setError(getErrorMessage(err, 'Nie udało się pobrać typów wizyt.'))
        }
      } finally {
        if (!cancelled) {
          setLoading(false)
        }
      }
    }
    void load()
    return () => {
      cancelled = true
    }
  }, [])

  async function onSubmit() {
    if (!selectedType) {
      setError('Wybierz typ wizyty.')
      return
    }
    const start = new Date(startLocal)
    if (Number.isNaN(start.getTime())) {
      setError('Podaj poprawną datę i godzinę (YYYY-MM-DDTHH:mm).')
      return
    }
    if (start.getTime() <= Date.now()) {
      setError('Termin musi być w przyszłości.')
      return
    }

    setBusy(true)
    setError(null)
    try {
      const startIso = start.toISOString()
      const endIso = addMinutesISO(startIso, selectedType.duration_min)
      const visit = await patientApi.requestVisit({
        therapy_type_id: selectedType.id,
        start_at: startIso,
        end_at: endIso,
        patient_note: note.trim(),
      })
      router.replace(`/visit/${visit.id}`)
    } catch (err) {
      setError(getErrorMessage(err, 'Nie udało się wysłać zgłoszenia.'))
    } finally {
      setBusy(false)
    }
  }

  return (
    <>
      <Stack.Screen options={{ title: 'Umów wizytę', headerShown: true }} />
      {loading ? (
        <LoadingBlock label="Ładowanie typów wizyt…" />
      ) : (
        <ScrollView style={styles.flex} contentContainerStyle={styles.content}>
          <Text style={styles.lead}>
            Wybierz typ i proponowany termin. Fizjoterapeuta zatwierdzi albo zaproponuje zmianę.
          </Text>

          {error ? <ErrorBanner message={error} /> : null}

          {types.length === 0 ? (
            <Text style={styles.muted}>Brak dostępnych typów wizyt u Twojego terapeuty.</Text>
          ) : (
            <View style={styles.typeList} accessibilityRole="radiogroup">
              <Text style={styles.label}>Typ wizyty</Text>
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
                      style={[styles.typeDot, { backgroundColor: type.color_hex || colors.primary }]}
                    />
                    <View style={styles.typeBody}>
                      <Text style={styles.typeName}>{type.name}</Text>
                      <Text style={styles.typeMeta}>{type.duration_min} min</Text>
                    </View>
                  </Pressable>
                )
              })}
            </View>
          )}

          <Field
            label="Proponowany start (YYYY-MM-DDTHH:mm)"
            value={startLocal}
            onChangeText={setStartLocal}
            autoCapitalize="none"
            hint={
              selectedType
                ? `Koniec wyliczymy automatycznie (${selectedType.duration_min} min).`
                : undefined
            }
          />

          <Field
            label="Notatka dla terapeuty (opcjonalnie)"
            value={note}
            onChangeText={setNote}
            multiline
            style={styles.note}
            hint="Np. preferowana pora, dolegliwości, pytania."
          />

          <Button
            title="Wyślij zgłoszenie"
            loading={busy}
            disabled={!therapyTypeId || types.length === 0}
            onPress={() => void onSubmit()}
          />
          <Button title="Anuluj" variant="ghost" onPress={() => router.back()} disabled={busy} />
        </ScrollView>
      )}
    </>
  )
}

const styles = StyleSheet.create({
  flex: { flex: 1, backgroundColor: colors.bg },
  content: { padding: space.lg, gap: space.base, paddingBottom: space['4xl'] },
  lead: { fontSize: typography.base, color: colors.ink, lineHeight: 22 },
  label: { fontSize: typography.sm, fontWeight: '600', color: colors.ink },
  muted: { fontSize: typography.sm, color: colors.muted },
  typeList: { gap: space.sm },
  typeTile: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: space.md,
    minHeight: 56,
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
