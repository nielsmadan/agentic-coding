import type { DevPhase, DevPhaseRecord, DevTopic } from '../types'
import { featureSuffix, isProvisional, NO_PHASE_LABEL } from '../core/phase'

export type PiColor = 'syntaxVariable' | 'thinkingMax' | 'warning' | 'mdLink' | 'accent' | 'success' | 'dim'

export type BandTheme = {
  style(text: string, options: { fg?: PiColor; bold?: boolean; dim?: boolean }): string
  fg(color: PiColor, text: string): string
}

export const PI_PHASE_COLOR = {
  planning: 'syntaxVariable',
  implementation: 'thinkingMax',
  'agent QA': 'warning',
  'QA fixes': 'warning',
  'code review': 'mdLink',
  'review fixes': 'mdLink',
  'manual QA': 'accent',
  'wrap-up': 'success',
} as const satisfies Record<DevPhase, PiColor>

export const bandLine = (theme: BandTheme, record: DevPhaseRecord | null, topic: DevTopic | null): string => {
  const feature = topic === null ? '' : theme.fg('dim', featureSuffix(topic))
  if (record === null) return `${theme.fg('dim', NO_PHASE_LABEL)}${feature}`
  const dim = isProvisional(record)
  return [
    theme.style('● ', { fg: PI_PHASE_COLOR[record.phase], dim }),
    theme.style(record.phase, { bold: true, dim }),
    feature,
  ].join('')
}
