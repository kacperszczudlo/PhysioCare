import { render, screen, fireEvent, act } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import { ToastProvider, useToast } from '../ui/ToastContext'
import { ToastContainer } from '../ui/ToastContainer'

function TestConsumer() {
  const { toast } = useToast()

  return (
    <div>
      <button onClick={() => toast.success('Operacja zakończona sukcesem', { title: 'Sukces' })}>
        Pokaż Sukces
      </button>
      <button onClick={() => toast.error('Wystąpił błąd podczas zapisywania')}>Pokaż Błąd</button>
      <button
        onClick={() =>
          toast.warning('Ostrzeżenie o braku danych', {
            action: { label: 'Cofnij', onClick: vi.fn() },
          })
        }
      >
        Pokaż Ostrzeżenie z Akcją
      </button>
    </div>
  )
}

describe('Toast Component System', () => {
  it('renders toasts when triggered from context', () => {
    render(
      <ToastProvider>
        <ToastContainer />
        <TestConsumer />
      </ToastProvider>,
    )

    fireEvent.click(screen.getByText('Pokaż Sukces'))

    expect(screen.getByText('Sukces')).toBeInTheDocument()
    expect(screen.getByText('Operacja zakończona sukcesem')).toBeInTheDocument()
    expect(screen.getByRole('status')).toBeInTheDocument()
  })

  it('renders error toasts with alert role for accessibility', () => {
    render(
      <ToastProvider>
        <ToastContainer />
        <TestConsumer />
      </ToastProvider>,
    )

    fireEvent.click(screen.getByText('Pokaż Błąd'))

    expect(screen.getByText('Wystąpił błąd podczas zapisywania')).toBeInTheDocument()
    expect(screen.getByRole('alert')).toBeInTheDocument()
  })

  it('dismisses toast when close button is clicked', async () => {
    vi.useFakeTimers()

    render(
      <ToastProvider>
        <ToastContainer />
        <TestConsumer />
      </ToastProvider>,
    )

    fireEvent.click(screen.getByText('Pokaż Sukces'))
    expect(screen.getByText('Operacja zakończona sukcesem')).toBeInTheDocument()

    const closeBtn = screen.getByLabelText('Zamknij powiadomienie')
    fireEvent.click(closeBtn)

    act(() => {
      vi.advanceTimersByTime(300)
    })

    expect(screen.queryByText('Operacja zakończona sukcesem')).not.toBeInTheDocument()

    vi.useRealTimers()
  })

  it('renders action button and triggers onClick when clicked', () => {
    const handleAction = vi.fn()

    function TestActionConsumer() {
      const { toast } = useToast()
      return (
        <button
          onClick={() =>
            toast.warning('Element usunięty', {
              action: { label: 'Cofnij', onClick: handleAction },
            })
          }
        >
          Usuń
        </button>
      )
    }

    render(
      <ToastProvider>
        <ToastContainer />
        <TestActionConsumer />
      </ToastProvider>,
    )

    fireEvent.click(screen.getByText('Usuń'))
    expect(screen.getByText('Cofnij')).toBeInTheDocument()

    fireEvent.click(screen.getByText('Cofnij'))
    expect(handleAction).toHaveBeenCalledTimes(1)
  })
})
