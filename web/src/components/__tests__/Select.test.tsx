import { render, screen, fireEvent } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import { Select } from '../ui/Select'

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
})
