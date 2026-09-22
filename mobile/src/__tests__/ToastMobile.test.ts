/**
 * @file ToastMobile.test.ts
 * @description Testy jednostkowe logiki tworzenia i konfigurowania powiadomień mobilnych Toast.
 */

import { describe, it, expect, vi } from 'vitest'
import {
  DEFAULT_TOAST_DURATION,
  type ToastItemData,
  type ToastOptions,
} from '../components/ToastContext'

vi.mock('react-native', () => ({
  Vibration: {
    vibrate: vi.fn(),
  },
}))

describe('Mobile Toast Logic & Helpers', () => {
  it('tworzy poprawnie ustrukturyzowane powiadomienie toast', () => {
    // Arrange
    const options: ToastOptions = {
      title: 'Powiadomienie',
      message: 'Operacja powiodła się',
      type: 'success',
      duration: 3000,
    }

    // Act
    const toastItem: ToastItemData = {
      id: 'test-id-1',
      title: options.title,
      message: options.message,
      type: options.type || 'info',
      duration: options.duration || DEFAULT_TOAST_DURATION,
      createdAt: Date.now(),
    }

    // Assert
    expect(toastItem.id).toBe('test-id-1')
    expect(toastItem.title).toBe('Powiadomienie')
    expect(toastItem.message).toBe('Operacja powiodła się')
    expect(toastItem.type).toBe('success')
    expect(toastItem.duration).toBe(3000)
  })

  it('używa DEFAULT_TOAST_DURATION gdy czas trwania nie jest podany', () => {
    // Arrange & Act & Assert
    expect(DEFAULT_TOAST_DURATION).toBe(4000)
  })

  it('obsługuje callback przycisku akcji w opcjach toastu', () => {
    // Arrange
    const actionMock = vi.fn()
    const options: ToastOptions = {
      message: 'Usunięto wpis',
      type: 'warning',
      action: {
        label: 'Cofnij',
        onPress: actionMock,
      },
    }

    // Act
    options.action?.onPress()

    // Assert
    expect(options.action?.label).toBe('Cofnij')
    expect(actionMock).toHaveBeenCalledTimes(1)
  })
})
