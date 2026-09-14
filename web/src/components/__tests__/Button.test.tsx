import { render, screen, fireEvent } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import { Button } from '../ui/Button'

describe('Button Component', () => {
  it('renders children correctly', () => {
    render(<Button>Zapisz</Button>)
    expect(screen.getByRole('button', { name: 'Zapisz' })).toBeInTheDocument()
  })

  it('triggers onClick handler when clicked', () => {
    const handleClick = vi.fn()
    render(<Button onClick={handleClick}>Zapisz</Button>)

    fireEvent.click(screen.getByRole('button', { name: 'Zapisz' }))
    expect(handleClick).toHaveBeenCalledTimes(1)
  })

  it('disables button and shows spinner when loading', () => {
    const handleClick = vi.fn()
    render(
      <Button loading onClick={handleClick}>
        Zapisz
      </Button>,
    )

    const btn = screen.getByRole('button')
    expect(btn).toBeDisabled()

    fireEvent.click(btn)
    expect(handleClick).not.toHaveBeenCalled()
  })
})
