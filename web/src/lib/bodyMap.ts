import type { BodyPartSlug } from 'simple-body-highlighter-react'

import type { BodyViewSide } from '@/api/types'

/** Rodzaj struktury anatomicznej poddawanej terapii. */
export type StructureKind = 'JOINT' | 'MUSCLE' | 'BONE' | 'SOFT'

/** Definicja celu terapeutycznego (struktury anatomicznej). */
export interface TreatmentTargetDef {
  /** Identyfikator celu. */
  id: string
  /** Czytelna polska nazwa struktury (np. "Staw kolanowy"). */
  label: string
  /** Typ struktury anatomicznej. */
  kind: StructureKind
}

/** Słownik polskich etykiet rodzajów struktur anatomicznych. */
export const STRUCTURE_KIND_LABELS: Record<StructureKind, string> = {
  JOINT: 'Stawy',
  MUSCLE: 'Mięśnie',
  BONE: 'Kości',
  SOFT: 'Tkanki miękkie',
}

/** Słownik charakterów i typów odczuwanego bólu pacjenta. */
export const PAIN_CHARACTERS = [
  { id: 'SHARP', label: 'Ostry' },
  { id: 'DULL', label: 'Tępy' },
  { id: 'BURNING', label: 'Pieczenie' },
  { id: 'THROBBING', label: 'Pulsujący' },
  { id: 'RADIATING', label: 'Promieniujący' },
  { id: 'STABBING', label: 'Kłujący' },
  { id: 'NUMBNESS', label: 'Drętwienie' },
] as const

/** Słownik etykiet statusów epizodu leczenia. */
export const EPISODE_STATUS_LABELS: Record<string, string> = {
  IN_PROGRESS: 'W trakcie',
  COMPLETED_SUCCESS: 'Zakończony sukcesem',
  REFERRED: 'Skierowany',
  INTERRUPTED: 'Przerwany',
}

export const REGION_LABELS: Record<BodyPartSlug, string> = {
  abs: 'Brzuch',
  head: 'Głowa',
  hair: 'Głowa (czaszka)',
  neck: 'Szyja',
  'left-neck': 'Szyja L',
  'right-neck': 'Szyja P',
  'left-trapezius': 'Czworoboczny L',
  'right-trapezius': 'Czworoboczny P',
  'left-deltoids': 'Naramienny L',
  'right-deltoids': 'Naramienny P',
  'left-chest': 'Klatka L',
  'right-chest': 'Klatka P',
  'left-biceps': 'Biceps L',
  'right-biceps': 'Biceps P',
  'left-triceps': 'Triceps L',
  'right-triceps': 'Triceps P',
  'left-forearm': 'Przedramię L',
  'right-forearm': 'Przedramię P',
  'left-hands': 'Dłoń L',
  'right-hands': 'Dłoń P',
  'left-obliques': 'Skośne brzucha L',
  'right-obliques': 'Skośne brzucha P',
  'left-upper-back': 'Plecy górne L',
  'right-upper-back': 'Plecy górne P',
  'left-lower-back': 'Plecy dolne L',
  'right-lower-back': 'Plecy dolne P',
  'left-gluteal': 'Pośladek L',
  'right-gluteal': 'Pośladek P',
  'left-adductors': 'Przywodziciele L',
  'right-adductors': 'Przywodziciele P',
  'left-quadriceps': 'Czworogłowy L',
  'right-quadriceps': 'Czworogłowy P',
  'left-hamstring': 'Tylna grupa uda L',
  'right-hamstring': 'Tylna grupa uda P',
  'left-knees': 'Kolano L',
  'right-knees': 'Kolano P',
  'left-calves': 'Łydka L',
  'right-calves': 'Łydka P',
  'left-tibialis': 'Piszczelowy przedni L',
  'right-tibialis': 'Piszczelowy przedni P',
  'left-ankles': 'Kostka L',
  'right-ankles': 'Kostka P',
  'left-feet': 'Stopa L',
  'right-feet': 'Stopa P',
}

const LEGACY_REGION_LABELS: Record<string, string> = {
  HEAD: 'Głowa',
  HEAD_L: 'Głowa L',
  HEAD_R: 'Głowa P',
  NECK: 'Szyja',
  CHEST: 'Klatka',
  CHEST_L: 'Klatka L',
  CHEST_R: 'Klatka P',
  ABDOMEN: 'Brzuch',
  ABDOMEN_L: 'Brzuch L',
  ABDOMEN_R: 'Brzuch P',
  UPPER_BACK: 'Plecy górne',
  UPPER_BACK_L: 'Plecy górne L',
  UPPER_BACK_R: 'Plecy górne P',
  MID_BACK_L: 'Plecy środkowe L',
  MID_BACK_R: 'Plecy środkowe P',
  LOWER_BACK: 'Plecy dolne',
  LOWER_BACK_L: 'Plecy dolne L',
  LOWER_BACK_R: 'Plecy dolne P',
  LUMBAR: 'Lędźwie',
  GLUTE_L: 'Pośladek L',
  GLUTE_R: 'Pośladek P',
  PELVIS_L: 'Miednica L',
  PELVIS_R: 'Miednica P',
  HIP_LEFT: 'Biodro L',
  HIP_RIGHT: 'Biodro P',
  THIGH_L: 'Udo L',
  THIGH_R: 'Udo P',
  THIGH_LEFT: 'Udo L',
  THIGH_RIGHT: 'Udo P',
  KNEE_L: 'Kolano L',
  KNEE_R: 'Kolano P',
  KNEE_LEFT: 'Kolano L',
  KNEE_RIGHT: 'Kolano P',
  SHIN_L: 'Podudzie L',
  SHIN_R: 'Podudzie P',
  SHIN_LEFT: 'Podudzie L',
  SHIN_RIGHT: 'Podudzie P',
  CALF_L: 'Łydka L',
  CALF_R: 'Łydka P',
  ANKLE_L: 'Kostka L',
  ANKLE_R: 'Kostka P',
  FOOT_L: 'Stopa L',
  FOOT_R: 'Stopa P',
  FOOT_LEFT: 'Stopa L',
  FOOT_RIGHT: 'Stopa P',
  SHOULDER_L: 'Bark L',
  SHOULDER_R: 'Bark P',
  SHOULDER_LEFT: 'Bark L',
  SHOULDER_RIGHT: 'Bark P',
  UPPER_ARM_L: 'Ramię L',
  UPPER_ARM_R: 'Ramię P',
  UPPER_ARM_LEFT: 'Ramię L',
  UPPER_ARM_RIGHT: 'Ramię P',
  ELBOW_L: 'Łokieć L',
  ELBOW_R: 'Łokieć P',
  FOREARM_L: 'Przedramię L',
  FOREARM_R: 'Przedramię P',
  FOREARM_LEFT: 'Przedramię L',
  FOREARM_RIGHT: 'Przedramię P',
  WRIST_L: 'Nadgarstek L',
  WRIST_R: 'Nadgarstek P',
  HAND_L: 'Dłoń L',
  HAND_R: 'Dłoń P',
  HAND_LEFT: 'Dłoń L',
  HAND_RIGHT: 'Dłoń P',
}

function bilateral(
  leftId: BodyPartSlug,
  rightId: BodyPartSlug,
  targets: (side: 'L' | 'R') => TreatmentTargetDef[],
): Record<string, TreatmentTargetDef[]> {
  return {
    [leftId]: targets('L'),
    [rightId]: targets('R'),
  }
}

export const REGION_TARGETS: Record<string, TreatmentTargetDef[]> = {
  head: [
    { id: 'TMJ', label: 'Staw skroniowo-żuchwowy', kind: 'JOINT' },
    { id: 'TEMPORALIS', label: 'M. skroniowy', kind: 'MUSCLE' },
    { id: 'MASSETER', label: 'M. żwacz', kind: 'MUSCLE' },
    { id: 'CRANIUM', label: 'Kości czaszki', kind: 'BONE' },
  ],
  hair: [
    { id: 'CRANIUM', label: 'Kości czaszki', kind: 'BONE' },
    { id: 'SCALP', label: 'Skóra głowy / powięź', kind: 'SOFT' },
  ],
  neck: [
    { id: 'C_SPINE', label: 'Kręgosłup szyjny (C1-C7)', kind: 'JOINT' },
    { id: 'SCM', label: 'M. mostkowo-obojczykowo-sutkowy', kind: 'MUSCLE' },
    { id: 'UPPER_TRAP', label: 'M. czworoboczny (góra)', kind: 'MUSCLE' },
    { id: 'LEVATOR_SCAP', label: 'M. dźwigacz łopatki', kind: 'MUSCLE' },
    { id: 'CERVICAL_DISC', label: 'Krążek międzykręgowy szyjny', kind: 'SOFT' },
  ],
  abs: [
    { id: 'RECTUS', label: 'M. prosty brzucha', kind: 'MUSCLE' },
    { id: 'TA', label: 'M. poprzeczny brzucha', kind: 'MUSCLE' },
    { id: 'LINEA_ALBA', label: 'Kresa biała / powięź', kind: 'SOFT' },
  ],
  ...bilateral('left-neck', 'right-neck', (s) => [
    { id: `C_SPINE`, label: 'Kręgosłup szyjny', kind: 'JOINT' },
    { id: `SCM_${s}`, label: `M. mostkowo-obojczykowo-sutkowy ${s}`, kind: 'MUSCLE' },
    { id: `LEVATOR_${s}`, label: `M. dźwigacz łopatki ${s}`, kind: 'MUSCLE' },
  ]),
  ...bilateral('left-trapezius', 'right-trapezius', (s) => [
    { id: `C_SPINE`, label: 'Kręgosłup szyjny / piersiowy', kind: 'JOINT' },
    { id: `TRAP_${s}`, label: `M. czworoboczny ${s}`, kind: 'MUSCLE' },
    { id: `SCAPULA_${s}`, label: `Łopatka ${s}`, kind: 'BONE' },
  ]),
  ...bilateral('left-deltoids', 'right-deltoids', (s) => [
    { id: `GH_${s}`, label: `Staw ramienny ${s}`, kind: 'JOINT' },
    { id: `AC_${s}`, label: `Staw barkowo-obojczykowy ${s}`, kind: 'JOINT' },
    { id: `DELT_${s}`, label: `M. naramienny ${s}`, kind: 'MUSCLE' },
    { id: `SUPRASPIN_${s}`, label: `M. nadgrzebieniowy ${s}`, kind: 'MUSCLE' },
    { id: `RC_TENDON_${s}`, label: `Ścięgna rotatorów ${s}`, kind: 'SOFT' },
  ]),
  ...bilateral('left-chest', 'right-chest', (s) => [
    { id: `SC_${s}`, label: `Staw mostkowo-obojczykowy ${s}`, kind: 'JOINT' },
    { id: `PEC_MAJ_${s}`, label: `M. piersiowy większy ${s}`, kind: 'MUSCLE' },
    { id: `PEC_MIN_${s}`, label: `M. piersiowy mniejszy ${s}`, kind: 'MUSCLE' },
    { id: `RIBS_${s}`, label: `Żebra ${s}`, kind: 'BONE' },
  ]),
  ...bilateral('left-biceps', 'right-biceps', (s) => [
    { id: `ELBOW_JT_${s}`, label: `Staw łokciowy ${s}`, kind: 'JOINT' },
    { id: `BICEPS_${s}`, label: `M. dwugłowy ramienia ${s}`, kind: 'MUSCLE' },
    { id: `BRACHIALIS_${s}`, label: `M. ramienny ${s}`, kind: 'MUSCLE' },
    { id: `HUMERUS_${s}`, label: `Kość ramienna ${s}`, kind: 'BONE' },
  ]),
  ...bilateral('left-triceps', 'right-triceps', (s) => [
    { id: `ELBOW_JT_${s}`, label: `Staw łokciowy ${s}`, kind: 'JOINT' },
    { id: `TRICEPS_${s}`, label: `M. trójgłowy ramienia ${s}`, kind: 'MUSCLE' },
    { id: `OLECRANON_${s}`, label: `Wyrostek łokciowy ${s}`, kind: 'BONE' },
  ]),
  ...bilateral('left-forearm', 'right-forearm', (s) => [
    { id: `WRIST_JT_${s}`, label: `Staw nadgarstkowy ${s}`, kind: 'JOINT' },
    { id: `WRIST_EXT_${s}`, label: `Prostowniki nadgarstka ${s}`, kind: 'MUSCLE' },
    { id: `WRIST_FLEX_${s}`, label: `Zginacze nadgarstka ${s}`, kind: 'MUSCLE' },
    { id: `RADIUS_${s}`, label: `Kość promieniowa ${s}`, kind: 'BONE' },
    { id: `ULNA_${s}`, label: `Kość łokciowa ${s}`, kind: 'BONE' },
  ]),
  ...bilateral('left-hands', 'right-hands', (s) => [
    { id: `MCP_${s}`, label: `Stawy MCP ${s}`, kind: 'JOINT' },
    { id: `THENAR_${s}`, label: `Mięśnie kłębu ${s}`, kind: 'MUSCLE' },
    { id: `METACARPALS_${s}`, label: `Kości śródręcza ${s}`, kind: 'BONE' },
  ]),
  ...bilateral('left-obliques', 'right-obliques', (s) => [
    { id: `OBLIQUE_${s}`, label: `M. skośne brzucha ${s}`, kind: 'MUSCLE' },
    { id: `QL_${s}`, label: `M. czworoboczny lędźwi ${s}`, kind: 'MUSCLE' },
    { id: `RIBS_${s}`, label: `Żebra ${s}`, kind: 'BONE' },
  ]),
  ...bilateral('left-upper-back', 'right-upper-back', (s) => [
    { id: `T_SPINE`, label: 'Kręgosłup piersiowy', kind: 'JOINT' },
    { id: `RHOMBOID_${s}`, label: `M. równoległoboczny ${s}`, kind: 'MUSCLE' },
    { id: `INFRASPIN_${s}`, label: `M. podgrzebieniowy ${s}`, kind: 'MUSCLE' },
    { id: `SCAPULA_${s}`, label: `Łopatka ${s}`, kind: 'BONE' },
  ]),
  ...bilateral('left-lower-back', 'right-lower-back', (s) => [
    { id: `L_SPINE`, label: 'Kręgosłup lędźwiowy', kind: 'JOINT' },
    { id: `QL_${s}`, label: `M. czworoboczny lędźwi ${s}`, kind: 'MUSCLE' },
    { id: `ERECTOR_${s}`, label: `Prostownik grzbietu ${s}`, kind: 'MUSCLE' },
    { id: `MULTIFIDUS_${s}`, label: `M. wielodzielny ${s}`, kind: 'MUSCLE' },
    { id: `LUMBAR_DISC`, label: 'Krążek międzykręgowy lędźwiowy', kind: 'SOFT' },
  ]),
  ...bilateral('left-gluteal', 'right-gluteal', (s) => [
    { id: `SI_${s}`, label: `Staw krzyżowo-biodrowy ${s}`, kind: 'JOINT' },
    { id: `GMAX_${s}`, label: `M. pośladkowy wielki ${s}`, kind: 'MUSCLE' },
    { id: `GMED_${s}`, label: `M. pośladkowy średni ${s}`, kind: 'MUSCLE' },
    { id: `PIRIFORMIS_${s}`, label: `M. gruszkowaty ${s}`, kind: 'MUSCLE' },
  ]),
  ...bilateral('left-adductors', 'right-adductors', (s) => [
    { id: `HIP_JT_${s}`, label: `Staw biodrowy ${s}`, kind: 'JOINT' },
    { id: `ADDUCTOR_${s}`, label: `Przywodziciele ${s}`, kind: 'MUSCLE' },
    { id: `PUBIS_${s}`, label: `Kość łonowa ${s}`, kind: 'BONE' },
  ]),
  ...bilateral('left-quadriceps', 'right-quadriceps', (s) => [
    { id: `HIP_JT_${s}`, label: `Staw biodrowy ${s}`, kind: 'JOINT' },
    { id: `KNEE_JT_${s}`, label: `Staw kolanowy ${s}`, kind: 'JOINT' },
    { id: `QUAD_${s}`, label: `M. czworogłowy ${s}`, kind: 'MUSCLE' },
    { id: `FEMUR_${s}`, label: `Kość udowa ${s}`, kind: 'BONE' },
  ]),
  ...bilateral('left-hamstring', 'right-hamstring', (s) => [
    { id: `HIP_JT_${s}`, label: `Staw biodrowy ${s}`, kind: 'JOINT' },
    { id: `KNEE_JT_${s}`, label: `Staw kolanowy ${s}`, kind: 'JOINT' },
    { id: `HAMSTRING_${s}`, label: `Tylna grupa uda ${s}`, kind: 'MUSCLE' },
    { id: `FEMUR_${s}`, label: `Kość udowa ${s}`, kind: 'BONE' },
  ]),
  ...bilateral('left-knees', 'right-knees', (s) => [
    { id: `KNEE_JT_${s}`, label: `Staw kolanowy ${s}`, kind: 'JOINT' },
    { id: `PF_${s}`, label: `Staw rzepkowo-udowy ${s}`, kind: 'JOINT' },
    { id: `MENISCUS_${s}`, label: `Łąkotki ${s}`, kind: 'SOFT' },
    { id: `ACL_${s}`, label: `Więzadło krzyżowe przednie ${s}`, kind: 'SOFT' },
    { id: `PATELLA_${s}`, label: `Rzepka ${s}`, kind: 'BONE' },
  ]),
  ...bilateral('left-calves', 'right-calves', (s) => [
    { id: `ANKLE_JT_${s}`, label: `Staw skokowy ${s}`, kind: 'JOINT' },
    { id: `GASTROC_${s}`, label: `M. brzuchaty łydki ${s}`, kind: 'MUSCLE' },
    { id: `SOLEUS_${s}`, label: `M. płaszczkowaty ${s}`, kind: 'MUSCLE' },
    { id: `ACHILLES_${s}`, label: `Ścięgno Achillesa ${s}`, kind: 'SOFT' },
  ]),
  ...bilateral('left-tibialis', 'right-tibialis', (s) => [
    { id: `TIBIALIS_ANT_${s}`, label: `M. piszczelowy przedni ${s}`, kind: 'MUSCLE' },
    { id: `TIBIA_${s}`, label: `Kość piszczelowa ${s}`, kind: 'BONE' },
    { id: `SHIN_SOFT_${s}`, label: `Powięź / okostna ${s}`, kind: 'SOFT' },
  ]),
  ...bilateral('left-ankles', 'right-ankles', (s) => [
    { id: `ANKLE_JT_${s}`, label: `Staw skokowy ${s}`, kind: 'JOINT' },
    { id: `ATFL_${s}`, label: `Więzadło ATFL ${s}`, kind: 'SOFT' },
    { id: `PERONEALS_${s}`, label: `M. strzałkowe ${s}`, kind: 'MUSCLE' },
    { id: `TALUS_${s}`, label: `Kość skokowa ${s}`, kind: 'BONE' },
  ]),
  ...bilateral('left-feet', 'right-feet', (s) => [
    { id: `MTP_${s}`, label: `Stawy MTP ${s}`, kind: 'JOINT' },
    { id: `PLANTAR_FASC_${s}`, label: `Rozcięgno podeszwowe ${s}`, kind: 'SOFT' },
    { id: `INTRINSIC_FOOT_${s}`, label: `Mięśnie stopy ${s}`, kind: 'MUSCLE' },
    { id: `METATARSALS_${s}`, label: `Kości śródstopia ${s}`, kind: 'BONE' },
  ]),
}

export const BODY_MODEL_COLORS = {
  defaultFill: '#c8d0d8',
} as const

export function vasColor(score: number): string {
  const t = Math.min(10, Math.max(0, score)) / 10
  const hue = 113 - t * 95
  const chroma = 0.08 + t * 0.1
  const light = 0.72 - t * 0.22
  return `oklch(${light.toFixed(3)} ${chroma.toFixed(3)} ${hue.toFixed(1)})`
}

export function regionLabel(regionId: string, _side?: BodyViewSide): string {
  if (regionId in REGION_LABELS) {
    return REGION_LABELS[regionId as BodyPartSlug]
  }
  return LEGACY_REGION_LABELS[regionId] ?? regionId
}

export function targetsForRegion(regionId: string): TreatmentTargetDef[] {
  return REGION_TARGETS[regionId] ?? []
}

export function targetLabel(targetId: string, regionId: string): string {
  const fromRegion = targetsForRegion(regionId).find((t) => t.id === targetId)
  if (fromRegion) return fromRegion.label
  for (const list of Object.values(REGION_TARGETS)) {
    const hit = list.find((t) => t.id === targetId)
    if (hit) return hit.label
  }
  return targetId
}

export function groupTargetsByKind(
  targets: TreatmentTargetDef[],
): Partial<Record<StructureKind, TreatmentTargetDef[]>> {
  const groups: Partial<Record<StructureKind, TreatmentTargetDef[]>> = {}
  for (const target of targets) {
    const bucket = groups[target.kind] ?? []
    bucket.push(target)
    groups[target.kind] = bucket
  }
  return groups
}

export function isBodyPartSlug(value: string): value is BodyPartSlug {
  return value in REGION_LABELS
}
