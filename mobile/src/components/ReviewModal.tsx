/**
 * @file ReviewModal.tsx
 * @description Modal umożliwiający wystawienie lub edycję opinii o fizjoterapeucie / wizycie.
 */

import React, { useEffect, useState } from 'react'
import {
  Modal,
  Pressable,
  ScrollView,
  StyleSheet,
  Switch,
  Text,
  TextInput,
  View,
} from 'react-native'
import { Ionicons } from '@expo/vector-icons'

import { Button } from '@/components/Button'
import { colors, radius, space, typography } from '@/theme/tokens'

interface ReviewModalProps {
  visible: boolean
  onClose: () => void
  onSubmit: (data: { rating: number; comment: string; is_anonymous: boolean }) => Promise<void>
  initialRating?: number
  initialComment?: string
  initialIsAnonymous?: boolean
  therapistName?: string
  title?: string
  isEdit?: boolean
}

const RATING_LABELS: Record<number, string> = {
  1: 'Bardzo słabo',
  2: 'Poniżej oczekiwań',
  3: 'W porządku',
  4: 'Bardzo dobrze',
  5: 'Znakomicie!',
}

export function ReviewModal({
  visible,
  onClose,
  onSubmit,
  initialRating = 0,
  initialComment = '',
  initialIsAnonymous = false,
  therapistName,
  title,
  isEdit = false,
}: ReviewModalProps) {
  const [rating, setRating] = useState(initialRating)
  const [comment, setComment] = useState(initialComment)
  const [isAnonymous, setIsAnonymous] = useState(initialIsAnonymous)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (visible) {
      setRating(initialRating)
      setComment(initialComment)
      setIsAnonymous(initialIsAnonymous)
      setError(null)
    }
  }, [visible, initialRating, initialComment, initialIsAnonymous])

  const handleSubmit = async () => {
    if (rating < 1 || rating > 5) {
      setError('Wybierz ocenę od 1 do 5 gwiazdek przed wysłaniem.')
      return
    }
    setError(null)
    setBusy(true)
    try {
      await onSubmit({ rating, comment: comment.trim(), is_anonymous: isAnonymous })
      onClose()
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Wystąpił błąd podczas zapisywania opinii.'
      setError(msg)
    } finally {
      setBusy(false)
    }
  }

  return (
    <Modal
      visible={visible}
      animationType="slide"
      transparent
      onRequestClose={onClose}
      accessibilityViewIsModal
    >
      <View style={styles.backdrop}>
        <View style={styles.sheet}>
          <ScrollView
            keyboardShouldPersistTaps="handled"
            contentContainerStyle={styles.content}
            showsVerticalScrollIndicator={false}
          >
            <View style={styles.header}>
              <View style={styles.headerTitleWrap}>
                <Text style={styles.title}>
                  {title || (isEdit ? 'Edytuj opinię' : 'Oceń fizjoterapeutę')}
                </Text>
                {therapistName ? <Text style={styles.subtitle}>{therapistName}</Text> : null}
              </View>
              <Pressable onPress={onClose} hitSlop={12} accessibilityLabel="Zamknij">
                <Ionicons name="close" size={24} color={colors.muted} />
              </Pressable>
            </View>

            {/* Wybór gwiazdek */}
            <View style={styles.starsContainer}>
              {[1, 2, 3, 4, 5].map((star) => {
                const isSelected = star <= rating
                return (
                  <Pressable
                    key={star}
                    onPress={() => setRating(star)}
                    style={styles.starButton}
                    hitSlop={8}
                    accessibilityLabel={`Ocena ${star} z 5`}
                  >
                    <Ionicons
                      name={isSelected ? 'star' : 'star-outline'}
                      size={36}
                      color={isSelected ? colors.warning : colors.border}
                    />
                  </Pressable>
                )
              })}
            </View>

            <Text style={[styles.ratingHint, rating === 0 && styles.ratingHintUnselected]}>
              {rating > 0 ? RATING_LABELS[rating] : 'Dotknij gwiazdki, aby wybrać ocenę'}
            </Text>

            {/* Komentarz */}
            <View style={styles.inputGroup}>
              <Text style={styles.inputLabel}>Twój komentarz (opcjonalnie)</Text>
              <TextInput
                style={styles.textArea}
                placeholder="Podziel się wrażeniami z wizyty, podejściem specjalisty lub efektami terapii..."
                placeholderTextColor={colors.muted}
                multiline
                numberOfLines={4}
                value={comment}
                onChangeText={setComment}
                maxLength={1000}
                textAlignVertical="top"
              />
            </View>

            {/* Anonimowość */}
            <View style={styles.switchRow}>
              <View style={styles.switchTextContainer}>
                <Text style={styles.switchLabel}>Wystaw opinię anonimowo</Text>
                <Text style={styles.switchDesc}>
                  Twoje imię i nazwisko nie będą widoczne publicznie.
                </Text>
              </View>
              <Switch
                value={isAnonymous}
                onValueChange={setIsAnonymous}
                trackColor={{ false: colors.border, true: colors.primary }}
                thumbColor={colors.surface}
              />
            </View>

            {error ? <Text style={styles.errorText}>{error}</Text> : null}

            <View style={styles.footer}>
              <Button
                title="Anuluj"
                variant="secondary"
                onPress={onClose}
                disabled={busy}
                style={styles.cancelBtn}
              />
              <Button
                title={isEdit ? 'Zapisz zmiany' : 'Opublikuj opinię'}
                variant="primary"
                onPress={() => void handleSubmit()}
                loading={busy}
                disabled={busy || rating === 0}
                style={styles.submitBtn}
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
    maxHeight: '90%',
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
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    gap: space.sm,
  },
  headerTitleWrap: {
    flex: 1,
  },
  title: {
    fontSize: typography.xl,
    fontWeight: '700',
    color: colors.ink,
  },
  subtitle: {
    fontSize: typography.sm,
    color: colors.primary,
    fontWeight: '600',
    marginTop: 2,
  },
  starsContainer: {
    flexDirection: 'row',
    justifyContent: 'center',
    gap: space.md,
    marginTop: space.xs,
  },
  starButton: {
    padding: space.xs,
  },
  ratingHint: {
    fontSize: typography.base,
    textAlign: 'center',
    color: colors.ink,
    fontWeight: '600',
    marginTop: -space.xs,
    marginBottom: space.xs,
  },
  ratingHintUnselected: {
    color: colors.muted,
    fontSize: typography.sm,
    fontWeight: '500',
  },
  inputGroup: {
    gap: space.xs,
  },
  inputLabel: {
    fontSize: typography.sm,
    color: colors.muted,
    fontWeight: '600',
  },
  textArea: {
    minHeight: 100,
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: radius.md,
    padding: space.md,
    fontSize: typography.base,
    color: colors.ink,
    textAlignVertical: 'top',
    backgroundColor: colors.surfaceMuted,
  },
  switchRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: space.xs,
  },
  switchTextContainer: {
    flex: 1,
    paddingRight: space.md,
  },
  switchLabel: {
    fontSize: typography.base,
    color: colors.ink,
    fontWeight: '600',
  },
  switchDesc: {
    fontSize: typography.sm,
    color: colors.muted,
    marginTop: 2,
  },
  errorText: {
    fontSize: typography.sm,
    color: colors.danger,
    textAlign: 'center',
  },
  footer: {
    flexDirection: 'row',
    gap: space.md,
    marginTop: space.sm,
  },
  cancelBtn: {
    flex: 1,
  },
  submitBtn: {
    flex: 2,
  },
})
