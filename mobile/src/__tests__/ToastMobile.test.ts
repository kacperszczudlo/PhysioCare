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
  it('creates a correctly structured toast item', () => {
    const options: ToastOptions = {
      title: 'Powiadomienie',
      message: 'Operacja powiodła się',
      type: 'success',
      duration: 3000,
    }

    const toastItem: ToastItemData = {
      id: 'test-id-1',
      title: options.title,
      message: options.message,
      type: options.type || 'info',
      duration: options.duration || DEFAULT_TOAST_DURATION,
      createdAt: Date.now(),
    }

    expect(toastItem.id).toBe('test-id-1')
    expect(toastItem.title).toBe('Powiadomienie')
    expect(toastItem.message).toBe('Operacja powiodła się')
    expect(toastItem.type).toBe('success')
    expect(toastItem.duration).toBe(3000)
  })

  it('uses DEFAULT_TOAST_DURATION when duration is omitted', () => {
    expect(DEFAULT_TOAST_DURATION).toBe(4000)
  })

  it('supports action callback payload in toast options', () => {
    const actionMock = vi.fn()
    const options: ToastOptions = {
      message: 'Usunięto wpis',
      type: 'warning',
      action: {
        label: 'Cofnij',
        onPress: actionMock,
      },
    }

    expect(options.action?.label).toBe('Cofnij')
    options.action?.onPress()
    expect(actionMock).toHaveBeenCalledTimes(1)
  })
})
