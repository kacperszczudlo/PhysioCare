export const colors = {
  bg: '#F3F4EF',
  surface: '#FFFFFF',
  surfaceMuted: '#EBEFD0',
  border: '#D7D8D0',
  borderStrong: '#B7B9AB',
  ink: '#1A1C11',
  muted: '#5D5F53',
  faint: '#696A60',
  primary: '#4E5200',
  primaryHover: '#3E4100',
  primarySubtle: '#EBEFD0',
  onPrimary: '#FFFFFF',
  accent: '#683B18',
  accentSubtle: '#FCE6D9',
  danger: '#B02A2D',
  dangerSubtle: '#FFE7E4',
  success: '#1E6626',
  successSubtle: '#DFF6DE',
  warning: '#A06200',
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
