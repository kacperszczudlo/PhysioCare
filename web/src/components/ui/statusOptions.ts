import type { EpisodeStatus } from '@/api/types'
import { EPISODE_STATUS_LABELS } from '@/lib/bodyMap'

export interface StatusOptionMeta {
  value: EpisodeStatus
  label: string
  pillClass: string
}

export const STATUS_OPTIONS_META: StatusOptionMeta[] = [
  {
    value: 'IN_PROGRESS',
    label: EPISODE_STATUS_LABELS['IN_PROGRESS'],
    pillClass: 'status-pill--in-progress',
  },
  {
    value: 'COMPLETED_SUCCESS',
    label: EPISODE_STATUS_LABELS['COMPLETED_SUCCESS'],
    pillClass: 'status-pill--completed',
  },
  {
    value: 'REFERRED',
    label: EPISODE_STATUS_LABELS['REFERRED'],
    pillClass: 'status-pill--referred',
  },
  {
    value: 'INTERRUPTED',
    label: EPISODE_STATUS_LABELS['INTERRUPTED'],
    pillClass: 'status-pill--interrupted',
  },
]
