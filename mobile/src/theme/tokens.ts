export const colors = {
  bg: '#F4F7F2',
  surface: '#FFFFFF',
  surfaceMuted: '#E8EEE4',
  border: '#D0D9CB',
  borderStrong: '#A8B8A0',
  ink: '#1F2A1C',
  muted: '#5C6B56',
  faint: '#6F7D69',
  primary: '#3D5C32',
  primaryHover: '#314D28',
  primarySubtle: '#E4EFE0',
  onPrimary: '#FFFFFF',
  accent: '#6B4F2A',
  accentSubtle: '#F3EBE0',
  danger: '#9B2C2C',
  dangerSubtle: '#FCE8E8',
  success: '#2F6B3A',
  successSubtle: '#E5F5E9',
  warning: '#8A6A1A',
} as const

export const space = {
  xs: 4,
  sm: 8,
  md: 12,
  base: 16,
  lg: 20,
  xl: 24,
  '2xl': 32,
  '3xl': 40,
  '4xl': 48,
} as const

export const radius = {
  sm: 6,
  md: 10,
  lg: 14,
} as const

export const typography = {
  xs: 12,
  sm: 14,
  base: 16,
  lg: 18,
  xl: 20,
  '2xl': 24,
  '3xl': 30,
} as const

/** Hit target floor - M3 / Web recommended (meets iOS 44). */
export const controlSize = 48

export const iconSize = {
  sm: 16,
  md: 20,
  lg: 24,
  xl: 32,
  '2xl': 48,
} as const

export const motion = {
  fast: 150,
  medium: 300,
  large: 400,
} as const
