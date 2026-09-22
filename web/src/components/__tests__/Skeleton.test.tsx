import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { Skeleton, SkeletonAvatar, SkeletonText, SkeletonWrapper } from '../ui/Skeleton'
import {
  AvailabilitySkeleton,
  DashboardSkeleton,
  DiagnosticMapSkeleton,
  MFASectionSkeleton,
  ModalFormSkeleton,
  PatientAssignmentsSkeleton,
  PatientsSkeleton,
} from '../skeletons/WebSkeletons'

/**
 * @file Skeleton.test.tsx
 * @description Zestaw testów jednostkowych dla komponentów ładowania szkieletowego (Skeleton primitives i WebSkeletons domenowe).
 */

describe('Web Skeleton Components', () => {
  it('renders base Skeleton primitive with custom dimensions', () => {
    const { container } = render(<Skeleton width="100px" height="20px" circle />)
    const el = container.querySelector('.skeleton')
    expect(el).toBeInTheDocument()
    expect(el).toHaveClass('skeleton--circle')
    expect(el).toHaveStyle({ width: '100px', height: '20px' })
  })

  it('renders SkeletonText with requested number of lines', () => {
    const { container } = render(<SkeletonText lines={4} />)
    const lines = container.querySelectorAll('.skeleton')
    expect(lines).toHaveLength(4)
  })

  it('renders SkeletonAvatar with dimension presets', () => {
    const { container } = render(<SkeletonAvatar size="lg" />)
    const avatar = container.querySelector('.skeleton--circle')
    expect(avatar).toBeInTheDocument()
    expect(avatar?.getAttribute('style')).toContain('3.5rem')
  })

  it('renders SkeletonWrapper with accessibility status attributes', () => {
    render(
      <SkeletonWrapper label="Ładowanie podglądu…">
        <Skeleton width="50px" height="10px" />
      </SkeletonWrapper>,
    )
    const status = screen.getByRole('status')
    expect(status).toBeInTheDocument()
    expect(status).toHaveAttribute('aria-busy', 'true')
    expect(status).toHaveAttribute('aria-label', 'Ładowanie podglądu…')
  })

  it('renders DashboardSkeleton without errors', () => {
    render(<DashboardSkeleton />)
    const status = screen.getByRole('status')
    expect(status).toHaveAttribute('aria-label', 'Ładowanie pulpitu…')
  })

  it('renders PatientsSkeleton without errors', () => {
    render(<PatientsSkeleton />)
    const status = screen.getByRole('status')
    expect(status).toHaveAttribute('aria-label', 'Ładowanie listy pacjentów…')
  })

  it('renders new domain skeletons without errors', () => {
    const { unmount: u1 } = render(<PatientAssignmentsSkeleton />)
    expect(screen.getByRole('status')).toHaveAttribute('aria-label', 'Ładowanie zaleceń…')
    u1()

    const { unmount: u2 } = render(<AvailabilitySkeleton />)
    expect(screen.getByRole('status')).toHaveAttribute('aria-label', 'Ładowanie grafiku pracy…')
    u2()

    const { unmount: u3 } = render(<DiagnosticMapSkeleton />)
    expect(screen.getByRole('status')).toHaveAttribute(
      'aria-label',
      'Ładowanie mapy diagnostycznej…',
    )
    u3()

    const { unmount: u4 } = render(<ModalFormSkeleton />)
    expect(screen.getByRole('status')).toHaveAttribute('aria-label', 'Ładowanie formularza…')
    u4()

    const { unmount: u5 } = render(<MFASectionSkeleton />)
    expect(screen.getByRole('status')).toHaveAttribute('aria-label', 'Ładowanie statusu MFA…')
    u5()
  })
})
