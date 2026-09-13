import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { PageHeader } from '../PageHeader';

describe('PageHeader Component', () => {
  it('renders title, description and actions correctly', () => {
    render(
      <PageHeader
        title="Harmonogram wizyt"
        description="Zarządzaj terminami i wizytami pacjentów."
        actions={<button>Nowa wizyta</button>}
      />
    );

    expect(screen.getByRole('heading', { level: 1, name: 'Harmonogram wizyt' })).toBeInTheDocument();
    expect(screen.getByText('Zarządzaj terminami i wizytami pacjentów.')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Nowa wizyta' })).toBeInTheDocument();
  });
});
