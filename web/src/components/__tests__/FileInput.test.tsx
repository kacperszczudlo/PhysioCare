import { render, screen, fireEvent } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import { FileInput } from '../ui/FileInput'

/**
 * @file FileInput.test.tsx
 * @description Zestaw testów dla komponentu wyboru i wgrywania plików z obsługą przeciągnij-i-upuść.
 */

describe('FileInput Component', () => {
  it('renders placeholder when no file is selected', () => {
    render(<FileInput file={null} onChange={vi.fn()} />)
    expect(screen.getByText('Wybierz plik PDF')).toBeInTheDocument()
    expect(screen.getByText('kliknij, aby wybrać dokument')).toBeInTheDocument()
  })

  it('renders selected file name and size', () => {
    const dummyFile = new File(['hello'], 'document.pdf', { type: 'application/pdf' })
    render(<FileInput file={dummyFile} onChange={vi.fn()} />)

    expect(screen.getByText('document.pdf')).toBeInTheDocument()
    expect(screen.getByTitle('Usuń wybrany plik')).toBeInTheDocument()
  })

  it('calls onChange(null) when clear button is clicked', () => {
    const handleChange = vi.fn()
    const dummyFile = new File(['hello'], 'document.pdf', { type: 'application/pdf' })
    render(<FileInput file={dummyFile} onChange={handleChange} />)

    fireEvent.click(screen.getByTitle('Usuń wybrany plik'))
    expect(handleChange).toHaveBeenCalledWith(null)
  })
})
