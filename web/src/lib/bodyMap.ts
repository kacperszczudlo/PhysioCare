import type { BodyViewSide } from '@/api/types'

export interface BodyRegionDef {
  id: string
  label: string
  /** SVG rect-ish hit area: x, y, w, h in viewBox 0 0 200 480 */
  x: number
  y: number
  w: number
  h: number
  rx?: number
}

export const PAIN_CHARACTERS = [
  { id: 'SHARP', label: 'Ostry' },
  { id: 'DULL', label: 'Tępy' },
  { id: 'BURNING', label: 'Pieczenie' },
  { id: 'THROBBING', label: 'Pulsujący' },
  { id: 'RADIATING', label: 'Promieniujący' },
  { id: 'STABBING', label: 'Kłujący' },
  { id: 'NUMBNESS', label: 'Drętwienie' },
] as const

export const EPISODE_STATUS_LABELS: Record<string, string> = {
  IN_PROGRESS: 'W trakcie',
  COMPLETED_SUCCESS: 'Zakończony sukcesem',
  REFERRED: 'Skierowany',
  INTERRUPTED: 'Przerwany',
}

/** Schematic front/back regions for Diagnostic Mapper (UC-13). */
export const BODY_REGIONS: Record<BodyViewSide, BodyRegionDef[]> = {
  FRONT: [
    { id: 'HEAD', label: 'Głowa', x: 78, y: 8, w: 44, h: 40, rx: 18 },
    { id: 'NECK', label: 'Szyja', x: 88, y: 48, w: 24, h: 18, rx: 6 },
    { id: 'SHOULDER_LEFT', label: 'Bark L', x: 42, y: 68, w: 36, h: 28, rx: 8 },
    { id: 'SHOULDER_RIGHT', label: 'Bark P', x: 122, y: 68, w: 36, h: 28, rx: 8 },
    { id: 'CHEST', label: 'Klatka', x: 70, y: 72, w: 60, h: 50, rx: 8 },
    { id: 'UPPER_ARM_LEFT', label: 'Ramię L', x: 28, y: 96, w: 24, h: 56, rx: 8 },
    { id: 'UPPER_ARM_RIGHT', label: 'Ramię P', x: 148, y: 96, w: 24, h: 56, rx: 8 },
    { id: 'ABDOMEN', label: 'Brzuch', x: 72, y: 122, w: 56, h: 48, rx: 8 },
    { id: 'FOREARM_LEFT', label: 'Przedramię L', x: 20, y: 152, w: 24, h: 52, rx: 8 },
    { id: 'FOREARM_RIGHT', label: 'Przedramię P', x: 156, y: 152, w: 24, h: 52, rx: 8 },
    { id: 'HIP_LEFT', label: 'Biodro L', x: 66, y: 170, w: 32, h: 28, rx: 8 },
    { id: 'HIP_RIGHT', label: 'Biodro P', x: 102, y: 170, w: 32, h: 28, rx: 8 },
    { id: 'HAND_LEFT', label: 'Dłoń L', x: 14, y: 204, w: 28, h: 24, rx: 8 },
    { id: 'HAND_RIGHT', label: 'Dłoń P', x: 158, y: 204, w: 28, h: 24, rx: 8 },
    { id: 'THIGH_LEFT', label: 'Udo L', x: 68, y: 198, w: 30, h: 70, rx: 10 },
    { id: 'THIGH_RIGHT', label: 'Udo P', x: 102, y: 198, w: 30, h: 70, rx: 10 },
    { id: 'KNEE_LEFT', label: 'Kolano L', x: 70, y: 268, w: 26, h: 22, rx: 8 },
    { id: 'KNEE_RIGHT', label: 'Kolano P', x: 104, y: 268, w: 26, h: 22, rx: 8 },
    { id: 'SHIN_LEFT', label: 'Podudzie L', x: 70, y: 290, w: 26, h: 70, rx: 8 },
    { id: 'SHIN_RIGHT', label: 'Podudzie P', x: 104, y: 290, w: 26, h: 70, rx: 8 },
    { id: 'FOOT_LEFT', label: 'Stopa L', x: 64, y: 360, w: 34, h: 22, rx: 8 },
    { id: 'FOOT_RIGHT', label: 'Stopa P', x: 102, y: 360, w: 34, h: 22, rx: 8 },
  ],
  BACK: [
    { id: 'HEAD', label: 'Głowa', x: 78, y: 8, w: 44, h: 40, rx: 18 },
    { id: 'NECK', label: 'Szyja', x: 88, y: 48, w: 24, h: 18, rx: 6 },
    { id: 'SHOULDER_LEFT', label: 'Bark L', x: 42, y: 68, w: 36, h: 28, rx: 8 },
    { id: 'SHOULDER_RIGHT', label: 'Bark P', x: 122, y: 68, w: 36, h: 28, rx: 8 },
    { id: 'UPPER_BACK', label: 'Plecy górne', x: 70, y: 72, w: 60, h: 50, rx: 8 },
    { id: 'UPPER_ARM_LEFT', label: 'Ramię L', x: 28, y: 96, w: 24, h: 56, rx: 8 },
    { id: 'UPPER_ARM_RIGHT', label: 'Ramię P', x: 148, y: 96, w: 24, h: 56, rx: 8 },
    { id: 'LOWER_BACK', label: 'Plecy dolne', x: 72, y: 122, w: 56, h: 48, rx: 8 },
    { id: 'FOREARM_LEFT', label: 'Przedramię L', x: 20, y: 152, w: 24, h: 52, rx: 8 },
    { id: 'FOREARM_RIGHT', label: 'Przedramię P', x: 156, y: 152, w: 24, h: 52, rx: 8 },
    { id: 'HIP_LEFT', label: 'Biodro L', x: 66, y: 170, w: 32, h: 28, rx: 8 },
    { id: 'HIP_RIGHT', label: 'Biodro P', x: 102, y: 170, w: 32, h: 28, rx: 8 },
    { id: 'HAND_LEFT', label: 'Dłoń L', x: 14, y: 204, w: 28, h: 24, rx: 8 },
    { id: 'HAND_RIGHT', label: 'Dłoń P', x: 158, y: 204, w: 28, h: 24, rx: 8 },
    { id: 'THIGH_LEFT', label: 'Udo L', x: 68, y: 198, w: 30, h: 70, rx: 10 },
    { id: 'THIGH_RIGHT', label: 'Udo P', x: 102, y: 198, w: 30, h: 70, rx: 10 },
    { id: 'KNEE_LEFT', label: 'Kolano L', x: 70, y: 268, w: 26, h: 22, rx: 8 },
    { id: 'KNEE_RIGHT', label: 'Kolano P', x: 104, y: 268, w: 26, h: 22, rx: 8 },
    { id: 'SHIN_LEFT', label: 'Podudzie L', x: 70, y: 290, w: 26, h: 70, rx: 8 },
    { id: 'SHIN_RIGHT', label: 'Podudzie P', x: 104, y: 290, w: 26, h: 70, rx: 8 },
    { id: 'FOOT_LEFT', label: 'Stopa L', x: 64, y: 360, w: 34, h: 22, rx: 8 },
    { id: 'FOOT_RIGHT', label: 'Stopa P', x: 102, y: 360, w: 34, h: 22, rx: 8 },
  ],
}

/** VAS 0–10 → olive→amber→red fill for map badges. */
export function vasColor(score: number): string {
  const t = Math.min(10, Math.max(0, score)) / 10
  const hue = 113 - t * 95
  const chroma = 0.08 + t * 0.1
  const light = 0.72 - t * 0.22
  return `oklch(${light.toFixed(3)} ${chroma.toFixed(3)} ${hue.toFixed(1)})`
}

export function regionLabel(regionId: string, side: BodyViewSide): string {
  return BODY_REGIONS[side].find((r) => r.id === regionId)?.label ?? regionId
}
