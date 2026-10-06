import { render, screen, fireEvent } from '@testing-library/react'
import { describe, it, expect, vi, beforeAll } from 'vitest'
import { Modal } from '../ui/Modal'

/**
 * @file Modal.test.tsx
 * @description Zestaw testów jednostkowych i dostępności WAI-ARIA dla uniwersalnego komponentu Modal.
 */

describe('Modal Component', () => {
  beforeAll(() => {
    // Mock HTMLDialogElement methods in jsdom
    HTMLDialogElement.prototype.showModal = vi.fn(function mockShowModal(this: HTMLDialogElement) {
      this.open = true
    })
    HTMLDialogElement.prototype.close = vi.fn(function mockClose(this: HTMLDialogElement) {
      this.open = false
    })
  })

  it('renders modal with title and description and connects aria attributes', () => {
    const handleClose = vi.fn()
    render(
      <Modal
        open={true}
        title="Testowy Modal"
        description="Opis pomocniczy dla screen readerów"
        onClose={handleClose}
      >
        <p>Zawartość okna modalnego</p>
      </Modal>,
    )

    const dialog = screen.getByRole('dialog')
    expect(dialog).toBeInTheDocument()

    const title = screen.getByRole('heading', { level: 2, name: 'Testowy Modal' })
    expect(title).toBeInTheDocument()

    const titleId = title.getAttribute('id')
    expect(dialog).toHaveAttribute('aria-labelledby', titleId)

    const desc = screen.getByText('Opis pomocniczy dla screen readerów')
    const descId = desc.getAttribute('id')
    expect(dialog).toHaveAttribute('aria-describedby', descId)

    expect(screen.getByText('Zawartość okna modalnego')).toBeInTheDocument()
  })

  it('calls onClose when close button is clicked', () => {
    const handleClose = vi.fn()
    render(
      <Modal open={true} title="Testowy Modal" onClose={handleClose}>
        <p>Treść</p>
      </Modal>,
    )

    const closeBtn = screen.getByRole('button', { name: 'Zamknij okno' })
    fireEvent.click(closeBtn)
    expect(handleClose).toHaveBeenCalledTimes(1)
  })

  it('calls onClose when backdrop is clicked', () => {
    const handleClose = vi.fn()
    render(
      <Modal open={true} title="Testowy Modal" onClose={handleClose}>
        <p>Treść</p>
      </Modal>,
    )

    const dialog = screen.getByRole('dialog')
    // Kliknięcie w dialog (backdrop)
    fireEvent.click(dialog)
    expect(handleClose).toHaveBeenCalledTimes(1)
  })

  it('does not close when clicking inside modal panel', () => {
    const handleClose = vi.fn()
    render(
      <Modal open={true} title="Testowy Modal" onClose={handleClose}>
        <button type="button">Wewnętrzny przycisk</button>
      </Modal>,
    )

    const insideBtn = screen.getByRole('button', { name: 'Wewnętrzny przycisk' })
    fireEvent.click(insideBtn)
    expect(handleClose).not.toHaveBeenCalled()
  })
})
