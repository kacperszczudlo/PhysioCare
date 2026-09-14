import type { CSSProperties, ReactNode } from 'react'
import './Skeleton.css'

export interface SkeletonProps {
  width?: string | number
  height?: string | number
  radius?: 'sm' | 'md' | 'lg' | 'full' | string | number
  circle?: boolean
  className?: string
  style?: CSSProperties
}

function formatDimension(value?: string | number): string | undefined {
  if (value === undefined) return undefined
  return typeof value === 'number' ? `${value}px` : value
}

export function Skeleton({
  width,
  height,
  radius,
  circle = false,
  className = '',
  style,
}: SkeletonProps) {
  const customStyle: CSSProperties = {
    ...style,
    width: formatDimension(width),
    height: formatDimension(height),
  }

  if (radius && !circle) {
    if (radius === 'sm') customStyle.borderRadius = 'var(--radius-sm)'
    else if (radius === 'md') customStyle.borderRadius = 'var(--radius-md)'
    else if (radius === 'lg') customStyle.borderRadius = 'var(--radius-lg)'
    else if (radius === 'full') customStyle.borderRadius = '9999px'
    else customStyle.borderRadius = formatDimension(radius)
  }

  const classes = ['skeleton', circle ? 'skeleton--circle' : '', className]
    .filter(Boolean)
    .join(' ')

  return <span className={classes} style={customStyle} aria-hidden="true" />
}

export interface SkeletonTextProps {
  lines?: number
  gap?: string | number
  className?: string
  lastLineWidth?: string
}

export function SkeletonText({
  lines = 3,
  gap,
  className = '',
  lastLineWidth = '65%',
}: SkeletonTextProps) {
  const lineArray = Array.from({ length: lines })

  return (
    <div
      className={`skeleton-text-group ${className}`.trim()}
      style={gap ? { gap: formatDimension(gap) } : undefined}
      aria-hidden="true"
    >
      {lineArray.map((_, index) => {
        const isLast = index === lines - 1 && lines > 1
        return (
          <Skeleton
            key={index}
            width={isLast ? lastLineWidth : '100%'}
            height="0.875rem"
            radius="sm"
          />
        )
      })}
    </div>
  )
}

export interface SkeletonAvatarProps {
  size?: 'sm' | 'md' | 'lg' | number
  className?: string
}

export function SkeletonAvatar({ size = 'md', className = '' }: SkeletonAvatarProps) {
  const dimensionMap = {
    sm: '2rem',
    md: '2.5rem',
    lg: '3.5rem',
  }
  const dimension = typeof size === 'number' ? `${size}px` : dimensionMap[size] || dimensionMap.md

  return <Skeleton circle width={dimension} height={dimension} className={className} />
}

export interface SkeletonWrapperProps {
  children: ReactNode
  label?: string
  className?: string
}

export function SkeletonWrapper({
  children,
  label = 'Ładowanie zawartości…',
  className = '',
}: SkeletonWrapperProps) {
  return (
    <div
      className={className}
      role="status"
      aria-busy="true"
      aria-live="polite"
      aria-label={label}
    >
      {children}
    </div>
  )
}
