import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { LoadingBlock, ErrorBanner, SuccessBanner, EmptyState } from '../AsyncState';

describe('AsyncState Components', () => {
  it('renders LoadingBlock with accessible role', () => {
    render(<LoadingBlock label="Ładowanie pacjentów..." />);
    expect(screen.getByRole('status')).toBeInTheDocument();
    expect(screen.getByText('Ładowanie pacjentów...')).toBeInTheDocument();
  });

  it('renders ErrorBanner and triggers retry callback', () => {
    const handleRetry = vi.fn();
    render(<ErrorBanner message="Nie udało się pobrać danych" onRetry={handleRetry} />);
    
    expect(screen.getByRole('alert')).toBeInTheDocument();
    expect(screen.getByText('Nie udało się pobrać danych')).toBeInTheDocument();
    
    const retryBtn = screen.getByRole('button', { name: 'Spróbuj ponownie' });
    fireEvent.click(retryBtn);
    expect(handleRetry).toHaveBeenCalledTimes(1);
  });

  it('renders SuccessBanner with message', () => {
    render(<SuccessBanner message="Zmiany zostały zapisane" />);
    expect(screen.getByRole('status')).toBeInTheDocument();
    expect(screen.getByText('Zmiany zostały zapisane')).toBeInTheDocument();
  });

  it('renders EmptyState with title and action button', () => {
    render(
      <EmptyState
        title="Brak wizyt"
        description="Nie masz zaplanowanych wizyt na ten dzień."
        action={<button>Dodaj wizytę</button>}
      />
    );
    expect(screen.getByText('Brak wizyt')).toBeInTheDocument();
    expect(screen.getByText('Nie masz zaplanowanych wizyt na ten dzień.')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Dodaj wizytę' })).toBeInTheDocument();
  });
});
