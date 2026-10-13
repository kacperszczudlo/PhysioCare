import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import { MemoryRouter } from 'react-router-dom'
import { AccountDeletionPage } from '../pages/AccountDeletionPage'

describe('AccountDeletionPage Component', () => {
  it('renders heading, store compliance notices and instructions', () => {
    render(
      <MemoryRouter>
        <AccountDeletionPage />
      </MemoryRouter>,
    )

    expect(screen.getByText('Usuwanie konta PhysioCare')).toBeInTheDocument()
    expect(
      screen.getByText('Wymóg Google Play Data Safety / Apple Account Deletion'),
    ).toBeInTheDocument()
    expect(screen.getByText('1. W aplikacji (zalecane)')).toBeInTheDocument()
    expect(screen.getByText('2. Bez aplikacji (ten URL)')).toBeInTheDocument()
    expect(screen.getByText('3. Co się dzieje z danymi')).toBeInTheDocument()
  })

  it('renders contact email for deletion requests without the mobile app', () => {
    render(
      <MemoryRouter>
        <AccountDeletionPage />
      </MemoryRouter>,
    )

    const emailLink = screen.getByRole('link', { name: /@/i })
    expect(emailLink).toHaveAttribute('href', expect.stringMatching(/^mailto:/))
  })

  it('renders links to privacy policy and login page', () => {
    render(
      <MemoryRouter>
        <AccountDeletionPage />
      </MemoryRouter>,
    )

    expect(screen.getByRole('link', { name: 'Polityka prywatności' })).toHaveAttribute(
      'href',
      '/privacy',
    )
    expect(screen.getByRole('link', { name: 'Logowanie' })).toHaveAttribute('href', '/login')
  })
})

