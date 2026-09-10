import { Modal, StyleSheet, Text, View } from 'react-native'

import { Button } from '@/components/Button'
import { colors, radius, space, typography } from '@/theme/tokens'

interface DataExportModalProps {
  open: boolean
  busy?: boolean
  onClose: () => void
  onConfirm: () => void
}

export function DataExportModal({
  open,
  busy = false,
  onClose,
  onConfirm,
}: DataExportModalProps) {
  function close() {
    if (!busy) {
      onClose()
    }
  }

  return (
    <Modal
      visible={open}
      animationType="slide"
      transparent
      onRequestClose={close}
      accessibilityViewIsModal
    >
      <View style={styles.backdrop}>
        <View style={styles.sheet}>
          <Text style={styles.title}>Eksport danych</Text>
          <Text style={styles.body}>
            Przygotujemy plik JSON z kopią Twoich danych (profil, zgody, wizyty, leczenie, metadane
            dokumentów, ćwiczenia, powiadomienia). Następnie zapiszesz go lub wyślesz sobie (Mail,
            Dyski, Pliki). Same pliki PDF i wideo nie są w archiwum — tylko linki; otwierasz je w
            aplikacji jak zwykle.
          </Text>
          <View style={styles.actions}>
            <Button title="Anuluj" variant="secondary" disabled={busy} onPress={close} />
            <Button title="Eksportuj" loading={busy} onPress={onConfirm} />
          </View>
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
    backgroundColor: colors.surface,
    borderTopLeftRadius: radius.lg,
    borderTopRightRadius: radius.lg,
    borderTopWidth: 1,
    borderColor: colors.border,
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
  actions: {
    gap: space.sm,
    marginTop: space.sm,
  },
})
