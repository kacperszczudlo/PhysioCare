import { useMemo, useState } from 'react'
import { FlatList, Modal, Pressable, StyleSheet, Text, TextInput, View } from 'react-native'

import {
  COUNTRIES,
  DEFAULT_COUNTRY_CODE,
  formatCountryOption,
  getCountryByCode,
} from '@/lib/countries'
import { colors, controlSize, radius, space, typography } from '@/theme/tokens'

interface PhoneFieldProps {
  label?: string
  countryCode: string
  nationalNumber: string
  onCountryChange: (countryCode: string) => void
  onNationalNumberChange: (nationalNumber: string) => void
  error?: string | null
  hint?: string
}

export function PhoneField({
  label = 'Telefon',
  countryCode,
  nationalNumber,
  onCountryChange,
  onNationalNumberChange,
  error,
  hint,
}: PhoneFieldProps) {
  const [pickerOpen, setPickerOpen] = useState(false)
  const [query, setQuery] = useState('')

  const country = getCountryByCode(countryCode) ?? getCountryByCode(DEFAULT_COUNTRY_CODE)!

  const filtered = useMemo(() => {
    const q = query.trim().toLocaleLowerCase('pl')
    if (!q) {
      return COUNTRIES
    }
    return COUNTRIES.filter(
      (item) =>
        item.name.toLocaleLowerCase('pl').includes(q) ||
        item.dial.includes(q) ||
        item.code.toLowerCase().includes(q),
    )
  }, [query])

  return (
    <View style={styles.wrap}>
      <Text style={styles.label}>{label}</Text>

      <Pressable
        accessibilityRole="button"
        accessibilityLabel={`Kraj: ${formatCountryOption(country)}`}
        onPress={() => setPickerOpen(true)}
        style={({ pressed }) => [
          styles.countryBtn,
          error ? styles.inputError : null,
          pressed ? styles.pressed : null,
        ]}
      >
        <Text style={styles.countryBtnText} numberOfLines={1}>
          {formatCountryOption(country)}
        </Text>
        <Text style={styles.chevron}>▼</Text>
      </Pressable>

      <View style={[styles.numberRow, error ? styles.inputError : null]}>
        <Text style={styles.prefix}>+{country.dial}</Text>
        <TextInput
          value={nationalNumber}
          onChangeText={onNationalNumberChange}
          keyboardType="phone-pad"
          autoComplete="tel"
          placeholder="512 345 678"
          placeholderTextColor={colors.faint}
          style={styles.numberInput}
        />
      </View>

      {error ? (
        <Text style={styles.error} accessibilityLiveRegion="polite">
          {error}
        </Text>
      ) : hint ? (
        <Text style={styles.hint}>{hint}</Text>
      ) : null}

      <Modal
        visible={pickerOpen}
        animationType="slide"
        presentationStyle="pageSheet"
        onRequestClose={() => setPickerOpen(false)}
      >
        <View style={styles.modal}>
          <View style={styles.modalHeader}>
            <Text style={styles.modalTitle}>Wybierz kraj</Text>
            <Pressable
              onPress={() => setPickerOpen(false)}
              hitSlop={8}
              style={styles.modalCloseBtn}
              accessibilityRole="button"
              accessibilityLabel="Zamknij"
            >
              <Text style={styles.modalClose}>Zamknij</Text>
            </Pressable>
          </View>
          <TextInput
            value={query}
            onChangeText={setQuery}
            placeholder="Szukaj kraju lub prefixu…"
            placeholderTextColor={colors.faint}
            autoCorrect={false}
            style={styles.search}
          />
          <FlatList
            data={filtered}
            keyExtractor={(item) => item.code}
            keyboardShouldPersistTaps="handled"
            renderItem={({ item }) => {
              const selected = item.code === country.code
              return (
                <Pressable
                  onPress={() => {
                    onCountryChange(item.code)
                    setPickerOpen(false)
                    setQuery('')
                  }}
                  style={({ pressed }) => [
                    styles.option,
                    selected ? styles.optionSelected : null,
                    pressed ? styles.pressed : null,
                  ]}
                >
                  <Text style={styles.optionText}>{item.name}</Text>
                  <Text style={styles.optionDial}>+{item.dial}</Text>
                </Pressable>
              )
            }}
          />
        </View>
      </Modal>
    </View>
  )
}

const styles = StyleSheet.create({
  wrap: { gap: space.sm },
  label: {
    fontSize: typography.sm,
    fontWeight: '600',
    color: colors.ink,
  },
  countryBtn: {
    minHeight: controlSize,
    borderWidth: 1.5,
    borderColor: colors.borderStrong,
    borderRadius: radius.md,
    backgroundColor: colors.surface,
    paddingHorizontal: space.md,
    flexDirection: 'row',
    alignItems: 'center',
    gap: space.sm,
  },
  countryBtnText: {
    flex: 1,
    color: colors.ink,
    fontSize: typography.base,
  },
  chevron: {
    color: colors.muted,
    fontSize: typography.xs,
  },
  numberRow: {
    minHeight: controlSize,
    borderWidth: 1.5,
    borderColor: colors.borderStrong,
    borderRadius: radius.md,
    backgroundColor: colors.surface,
    paddingHorizontal: space.md,
    flexDirection: 'row',
    alignItems: 'center',
    gap: space.sm,
  },
  prefix: {
    color: colors.muted,
    fontWeight: '700',
    fontSize: typography.sm,
  },
  numberInput: {
    flex: 1,
    color: colors.ink,
    fontSize: typography.base,
    paddingVertical: space.sm,
  },
  inputError: {
    borderColor: colors.danger,
  },
  pressed: {
    opacity: 0.85,
  },
  error: {
    color: colors.danger,
    fontSize: typography.sm,
  },
  hint: {
    color: colors.muted,
    fontSize: typography.sm,
  },
  modal: {
    flex: 1,
    backgroundColor: colors.bg,
    paddingTop: space.lg,
  },
  modalHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: space.xl,
    marginBottom: space.md,
  },
  modalTitle: {
    fontSize: typography.xl,
    fontWeight: '700',
    color: colors.ink,
  },
  modalCloseBtn: {
    minHeight: controlSize,
    minWidth: controlSize,
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: space.sm,
  },
  modalClose: {
    color: colors.primary,
    fontWeight: '600',
    fontSize: typography.base,
    textDecorationLine: 'underline',
  },
  search: {
    marginHorizontal: space.xl,
    marginBottom: space.md,
    minHeight: controlSize,
    borderWidth: 1.5,
    borderColor: colors.borderStrong,
    borderRadius: radius.md,
    backgroundColor: colors.surface,
    paddingHorizontal: space.md,
    color: colors.ink,
    fontSize: typography.base,
  },
  option: {
    paddingHorizontal: space.xl,
    paddingVertical: space.md,
    minHeight: controlSize,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    gap: space.md,
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: colors.border,
  },
  optionSelected: {
    backgroundColor: colors.primarySubtle,
  },
  optionText: {
    flex: 1,
    color: colors.ink,
    fontSize: typography.base,
  },
  optionDial: {
    color: colors.muted,
    fontWeight: '600',
    fontSize: typography.sm,
  },
})
