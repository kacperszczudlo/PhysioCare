/**
 * @file tokens.ts
 * @description Tokeny projektowe (Design Tokens) interfejsu użytkownika aplikacji mobilnej – kolory, odstępy, promienie zaokrągleń, typografia oraz stałe czasowe animacji.
 */

/** Paleta kolorów motywu aplikacji PhysioCare */
export const colors = {
  /** Kolor tła głównego aplikacji */
  bg: '#F3F4EF',
  /** Kolor powierzchni kart i kontenerów */
  surface: '#FFFFFF',
  /** Wyciszony kolor powierzchni */
  surfaceMuted: '#EBEFD0',
  /** Kolor krawędzi i obramowań */
  border: '#D7D8D0',
  /** Mocniejszy kolor obramowania */
  borderStrong: '#B7B9AB',
  /** Kolor tekstu podstawowego */
  ink: '#1A1C11',
  /** Wyciszony kolor tekstu */
  muted: '#5D5F53',
  /** Subtelny kolor tekstu pomocniczego */
  faint: '#696A60',
  /** Główny kolor marki */
  primary: '#4E5200',
  /** Kolor po wciśnięciu/najechaniu na element główny */
  primaryHover: '#3E4100',
  /** Subtelne tło nawiązujące do koloru głównego */
  primarySubtle: '#EBEFD0',
  /** Kolor tekstu na tle koloru głównego */
  onPrimary: '#FFFFFF',
  /** Akcentujący kolor poboczny */
  accent: '#683B18',
  /** Subtelne tło akcentujące */
  accentSubtle: '#FCE6D9',
  /** Kolor błędów i ostrzeżeń krytycznych */
  danger: '#B02A2D',
  /** Subtelne tło dla komunikatów błędów */
  dangerSubtle: '#FFE7E4',
  /** Kolor sukcesu i zaliczenia */
  success: '#1E6626',
  /** Subtelne tło dla komunikatów sukcesu */
  successSubtle: '#DFF6DE',
  /** Kolor ostrzegawczy */
  warning: '#A06200',
} as const

/** Skala odstępów wewnętrznych i zewnętrznych (padding / margin) */
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

/** Promienie zaokrąglenia narożników elementów (border-radius) */
export const radius = {
  sm: 6,
  md: 10,
  lg: 14,
} as const

/** Skala rozmiarów czcionki w pikselach */
export const typography = {
  xs: 12,
  sm: 14,
  base: 16,
  lg: 18,
  xl: 20,
  '2xl': 24,
  '3xl': 30,
} as const

/** Minimalna powierzchnia klikalna elementu interaktywnego (zgodna z HIG / Material Design 48pt) */
export const controlSize = 48

/** Skala rozmiarów ikonek w pikselach */
export const iconSize = {
  sm: 16,
  md: 20,
  lg: 24,
  xl: 32,
  '2xl': 48,
} as const

/** Czas trwania animacji w milisekundach */
export const motion = {
  fast: 150,
  medium: 300,
  large: 400,
} as const

