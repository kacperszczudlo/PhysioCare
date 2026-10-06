import { render, screen, fireEvent } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import { Select } from '../ui/Select'

/**
 * @file Select.test.tsx
 * @description Zestaw testów dostępności i nawigacji klawiaturą dla spersonalizowanego komponentu rozwijalnego Select.
 */

describe('Select Component', () => {
  const options = [
    { value: 'MRI', label: 'Sugestia MRI' },
    { value: 'TK', label: 'Sugestia TK' },
    { value: 'USG', label: 'Sugestia USG' },
  ]

  it('renders selected option label', () => {
    render(<Select value="MRI" onChange={vi.fn()} options={options} />)
    expect(screen.getByText('Sugestia MRI')).toBeInTheDocument()
  })

  it('opens popover and selects new option', () => {
    const handleChange = vi.fn()
    render(<Select value="MRI" onChange={handleChange} options={options} />)

    fireEvent.click(screen.getByRole('button'))
    expect(screen.getByRole('listbox')).toBeInTheDocument()

    fireEvent.click(screen.getByText('Sugestia USG'))
    expect(handleChange).toHaveBeenCalledWith('USG')
  })

  it('handles keyboard navigation', () => {
    const handleChange = vi.fn()
    render(<Select value="MRI" onChange={handleChange} options={options} />)

    const btn = screen.getByRole('button')
    fireEvent.keyDown(btn, { key: 'ArrowDown' })
    fireEvent.keyDown(btn, { key: 'ArrowDown' })
    fireEvent.keyDown(btn, { key: 'Enter' })

    expect(handleChange).toHaveBeenCalledWith('TK')
  })

  it('supports Home and End keys for jumping through options', () => {
    const handleChange = vi.fn()
    render(<Select value="TK" onChange={handleChange} options={options} />)

    const btn = screen.getByRole('button')
    fireEvent.click(btn)

    fireEvent.keyDown(btn, { key: 'End' })
    fireEvent.keyDown(btn, { key: 'Enter' })
    expect(handleChange).toHaveBeenCalledWith('USG')

    fireEvent.click(btn)
    fireEvent.keyDown(btn, { key: 'Home' })
    fireEvent.keyDown(btn, { key: 'Enter' })
    expect(handleChange).toHaveBeenCalledWith('MRI')
  })

  it('closes popover on Escape key and updates ARIA attributes', () => {
    render(<Select value="MRI" onChange={vi.fn()} options={options} />)
    const btn = screen.getByRole('button')

    expect(btn).toHaveAttribute('aria-expanded', 'false')
    expect(btn).not.toHaveAttribute('aria-controls')

    fireEvent.click(btn)
    expect(btn).toHaveAttribute('aria-expanded', 'true')
    const listboxId = btn.getAttribute('aria-controls')
    expect(listboxId).toBeTruthy()
    expect(btn.getAttribute('aria-activedescendant')).toContain('MRI')

    fireEvent.keyDown(btn, { key: 'Escape' })
    expect(btn).toHaveAttribute('aria-expanded', 'false')
    expect(screen.queryByRole('listbox')).not.toBeInTheDocument()
  })

  it('safely handles empty options list without NaN or errors', () => {
    render(<Select value="" onChange={vi.fn()} options={[]} placeholder="Brak danych" />)
    const btn = screen.getByRole('button')
    fireEvent.click(btn)
    expect(screen.getByRole('listbox')).toBeInTheDocument()
    expect(screen.getByText('Brak dostępnych opcji')).toBeInTheDocument()

    // Navigating empty options doesn't crash
    fireEvent.keyDown(btn, { key: 'ArrowDown' })
    fireEvent.keyDown(btn, { key: 'Enter' })
    fireEvent.keyDown(btn, { key: 'Escape' })
    expect(screen.queryByRole('listbox')).not.toBeInTheDocument()
  })
})
