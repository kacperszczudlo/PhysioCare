import { useMemo, useState } from 'react'
import {
  Modal,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from 'react-native'

import { Button } from '@/components/Button'
import { colors, radius, space, typography } from '@/theme/tokens'

export const DELETION_REASON_OPTIONS = [
  { id: 'not_using', label: 'Nie korzystam z aplikacji' },
  { id: 'technical', label: 'Problemy techniczne' },
  { id: 'therapist_change', label: 'Zmiana fizjoterapeuty / gabinetu' },
  { id: 'privacy', label: 'Obawy o prywatność danych' },
  { id: 'other', label: 'Inny powód' },
] as const

type ReasonId = (typeof DELETION_REASON_OPTIONS)[number]['id']

interface AccountDeletionModalProps {
  open: boolean
  busy?: boolean
  onClose: () => void
  onConfirm: (reason: string) => Promise<void>
}

export function AccountDeletionModal({
  open,
  busy = false,
  onClose,
  onConfirm,
}: AccountDeletionModalProps) {
  const [reasonId, setReasonId] = useState<ReasonId | null>(null)
  const [otherText, setOtherText] = useState('')
  const [confirmed, setConfirmed] = useState(false)
  const [localError, setLocalError] = useState<string | null>(null)

  const reasonPayload = useMemo(() => {
    if (!reasonId) {
      return ''
    }
    const label = DELETION_REASON_OPTIONS.find((o) => o.id === reasonId)?.label ?? reasonId
    if (reasonId === 'other') {
      const detail = otherText.trim()
      return detail ? `${label}: ${detail}` : label
    }
    return label
  }, [reasonId, otherText])

  function resetAndClose() {
    if (busy) {
      return
    }
    setReasonId(null)
    setOtherText('')
    setConfirmed(false)
    setLocalError(null)
    onClose()
  }

  async function submit() {
    setLocalError(null)
    if (!reasonId) {
      setLocalError('Wybierz powód rezygnacji.')
      return
    }
    if (reasonId === 'other' && !otherText.trim()) {
      setLocalError('Opisz krótko powód rezygnacji.')
      return
    }
    if (!confirmed) {
      setLocalError('Potwierdź, że na pewno chcesz usunąć konto.')
      return
    }
    await onConfirm(reasonPayload)
  }

  return (
    <Modal
      visible={open}
      animationType="slide"
      transparent
      onRequestClose={resetAndClose}
      accessibilityViewIsModal
    >
      <View style={styles.backdrop}>
        <View style={styles.sheet}>
          <ScrollView
            keyboardShouldPersistTaps="handled"
            contentContainerStyle={styles.content}
          >
            <Text style={styles.title}>Usunąć konto?</Text>
            <Text style={styles.body}>
              Konto zostanie wyłączone, a dane osobowe zanonimizowane. Adres e-mail będzie wolny -
              będziesz mógł założyć nowe konto tym samym adresem. Tej operacji nie cofniesz z poziomu
              aplikacji.
            </Text>

            <Text style={styles.sectionLabel}>Dlaczego rezygnujesz?</Text>
            {DELETION_REASON_OPTIONS.map((option) => {
              const selected = reasonId === option.id
              return (
                <Pressable
                  key={option.id}
                  accessibilityRole="radio"
                  accessibilityState={{ selected }}
                  onPress={() => setReasonId(option.id)}
                  style={[styles.option, selected ? styles.optionSelected : null]}
                >
                  <View style={[styles.radio, selected ? styles.radioSelected : null]} />
                  <Text style={styles.optionLabel}>{option.label}</Text>
                </Pressable>
              )
            })}

            {reasonId === 'other' ? (
              <TextInput
                value={otherText}
                onChangeText={setOtherText}
                placeholder="Napisz krótko, co możemy poprawić…"
                placeholderTextColor={colors.faint}
                multiline
                numberOfLines={3}
                style={styles.textarea}
                editable={!busy}
              />
            ) : null}

            <Pressable
              accessibilityRole="checkbox"
              accessibilityState={{ checked: confirmed }}
              onPress={() => setConfirmed((v) => !v)}
              style={styles.confirmRow}
            >
              <View style={[styles.checkbox, confirmed ? styles.checkboxChecked : null]}>
                {confirmed ? <Text style={styles.checkmark}>✓</Text> : null}
              </View>
              <Text style={styles.confirmLabel}>
                Rozumiem i na pewno chcę usunąć konto PhysioCare
              </Text>
            </Pressable>

            {localError ? <Text style={styles.error}>{localError}</Text> : null}

            <View style={styles.actions}>
              <Button
                title="Anuluj"
                variant="secondary"
                disabled={busy}
                onPress={resetAndClose}
              />
              <Button
                title="Usuń konto na zawsze"
                variant="danger"
                loading={busy}
                onPress={() => void submit()}
              />
            </View>
          </ScrollView>
        </View>
      </View>
    </Modal>
  )
}

const styles = StyleSheet.create({
  backdrop: {
    flex: 1,
    backgroundColor: 'rgba(31, 42, 28, 0.45)',
    justifyContent: 'flex-end',
  },
  sheet: {
    maxHeight: '92%',
    backgroundColor: colors.surface,
    borderTopLeftRadius: radius.lg,
    borderTopRightRadius: radius.lg,
    borderTopWidth: 1,
    borderColor: colors.border,
  },
  content: {
    padding: space.xl,
    gap: space.md,
    paddingBottom: space['3xl'],
  },
  title: {
    fontSize: typography.xl,
    fontWeight: '700',
    color: colors.ink,
  },
  body: {
    fontSize: typography.sm,
    lineHeight: 20,
    color: colors.muted,
  },
  sectionLabel: {
    marginTop: space.sm,
    fontSize: typography.sm,
    fontWeight: '600',
    color: colors.ink,
  },
  option: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: space.md,
    paddingVertical: space.md,
    paddingHorizontal: space.base,
    borderRadius: radius.md,
    borderWidth: 1,
    borderColor: colors.border,
    backgroundColor: colors.surface,
  },
  optionSelected: {
    borderColor: colors.primary,
    backgroundColor: colors.primarySubtle,
  },
  radio: {
    width: 18,
    height: 18,
    borderRadius: 9,
    borderWidth: 2,
    borderColor: colors.borderStrong,
  },
  radioSelected: {
    borderColor: colors.primary,
    backgroundColor: colors.primary,
  },
  optionLabel: {
    flex: 1,
    fontSize: typography.base,
    color: colors.ink,
  },
  textarea: {
    minHeight: 88,
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: radius.md,
    padding: space.md,
    fontSize: typography.base,
    color: colors.ink,
    textAlignVertical: 'top',
    backgroundColor: colors.surfaceMuted,
  },
  confirmRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: space.md,
    marginTop: space.sm,
  },
  checkbox: {
    width: 22,
    height: 22,
    borderRadius: 4,
    borderWidth: 2,
    borderColor: colors.borderStrong,
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: 2,
  },
  checkboxChecked: {
    borderColor: colors.danger,
    backgroundColor: colors.danger,
  },
  checkmark: {
    color: colors.onPrimary,
    fontSize: 14,
    fontWeight: '700',
    lineHeight: 16,
  },
  confirmLabel: {
    flex: 1,
    fontSize: typography.sm,
    lineHeight: 20,
    color: colors.ink,
  },
  error: {
    color: colors.danger,
    fontSize: typography.sm,
  },
  actions: {
    gap: space.sm,
    marginTop: space.sm,
  },
})
