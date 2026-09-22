/**
 * @file ToastContainer.tsx
 * @description Kontener warstwy powiadomień toast (pozycjonowany bezwzględnie na górze ekranu).
 */

import React from 'react'
import { StyleSheet, View } from 'react-native'
import { useSafeAreaInsets } from 'react-native-safe-area-context'

import { space } from '@/theme/tokens'
import { useToast } from './ToastContext'
import { ToastItem } from './ToastItem'

/**
 * Komponent renderujący aktywną listę powiadomień mobilnych na górze ekranu z uwzględnieniem bezpiecznych obszarów (Safe Area).
 *
 * @returns Element React Native zawierający powiadomienia lub null.
 */
export function ToastContainer() {
  const { toasts, removeToast } = useToast()
  const insets = useSafeAreaInsets()

  if (toasts.length === 0) return null

  return (
    <View
      style={[styles.container, { top: Math.max(insets.top + space.sm, space.base) }]}
      pointerEvents="box-none"
    >
      {toasts.map((t) => (
        <ToastItem key={t.id} toast={t} onClose={removeToast} />
      ))}
    </View>
  )
}

const styles = StyleSheet.create({
  container: {
    position: 'absolute',
    left: space.base,
    right: space.base,
    zIndex: 9999,
  },
})
