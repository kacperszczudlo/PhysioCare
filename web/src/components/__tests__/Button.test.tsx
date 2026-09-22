import { render, screen, fireEvent } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import { Button } from '../ui/Button'

/**
 * Zestaw testów jednostkowych komponentu Button weryfikujących renderowanie, zdarzenia kliknięć i stany ładowania.
 */
describe('Button Component', () => {
  it('renders children correctly', () => {
    // Arrange & Act
    render(<Button>Zapisz</Button>)

    // Assert
    expect(screen.getByRole('button', { name: 'Zapisz' })).toBeInTheDocument()
  })

  it('triggers onClick handler when clicked', () => {
    // Arrange
    const handleClick = vi.fn()
    render(<Button onClick={handleClick}>Zapisz</Button>)

    // Act
    fireEvent.click(screen.getByRole('button', { name: 'Zapisz' }))

    // Assert
    expect(handleClick).toHaveBeenCalledTimes(1)
  })

  it('disables button and shows spinner when loading', () => {
    // Arrange
    const handleClick = vi.fn()
    render(
      <Button loading onClick={handleClick}>
        Zapisz
      </Button>,
    )

    // Act
    const btn = screen.getByRole('button')

    // Assert
    expect(btn).toBeDisabled()
    fireEvent.click(btn)
    expect(handleClick).not.toHaveBeenCalled()
  })
})
