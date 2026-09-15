import { render, screen, fireEvent } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import { StatusSelect } from '../ui/StatusSelect'
import type { EpisodeStatus } from '@/api/types'

describe('StatusSelect Component', () => {
  it('renders selected status label correctly', () => {
    render(<StatusSelect value="IN_PROGRESS" onChange={vi.fn()} />)
    expect(screen.getByText('W trakcie')).toBeInTheDocument()
  })

  it('opens popover options on trigger click', () => {
    render(<StatusSelect value="IN_PROGRESS" onChange={vi.fn()} />)
    const trigger = screen.getByRole('button', { name: 'Wybierz status epizodu' })
    expect(trigger).toHaveAttribute('aria-expanded', 'false')

    fireEvent.click(trigger)
    expect(trigger).toHaveAttribute('aria-expanded', 'true')
    expect(screen.getByRole('listbox')).toBeInTheDocument()
    expect(screen.getByText('Zakończony sukcesem')).toBeInTheDocument()
    expect(screen.getByText('Skierowany')).toBeInTheDocument()
    expect(screen.getByText('Przerwany')).toBeInTheDocument()
  })

  it('calls onChange with new status when an option is clicked', () => {
    const handleChange = vi.fn()
    render(<StatusSelect value="IN_PROGRESS" onChange={handleChange} />)

    fireEvent.click(screen.getByRole('button'))
    fireEvent.click(screen.getByText('Zakończony sukcesem'))

    expect(handleChange).toHaveBeenCalledWith('COMPLETED_SUCCESS' as EpisodeStatus)
    expect(screen.queryByRole('listbox')).not.toBeInTheDocument()
  })

  it('navigates options and selects using keyboard', () => {
    const handleChange = vi.fn()
    render(<StatusSelect value="IN_PROGRESS" onChange={handleChange} />)

    const trigger = screen.getByRole('button')
    fireEvent.keyDown(trigger, { key: 'ArrowDown' })
    expect(screen.getByRole('listbox')).toBeInTheDocument()

    fireEvent.keyDown(trigger, { key: 'ArrowDown' })
    fireEvent.keyDown(trigger, { key: 'Enter' })

    expect(handleChange).toHaveBeenCalledWith('COMPLETED_SUCCESS' as EpisodeStatus)
  })

  it('does not open when disabled', () => {
    const handleChange = vi.fn()
    render(<StatusSelect value="IN_PROGRESS" onChange={handleChange} disabled />)

    const trigger = screen.getByRole('button')
    expect(trigger).toBeDisabled()

    fireEvent.click(trigger)
    expect(screen.queryByRole('listbox')).not.toBeInTheDocument()
  })
})
