import type { DevChecks } from '../types'
import { checkItems } from '../core/checklist'
import type { CheckItem } from '../core/checklist'

export type PiColor = CheckItem['color']

export type BandTheme = {
  fg(color: PiColor, text: string): string
}

export const bandLine = (theme: BandTheme, checks: DevChecks): string =>
  checkItems(checks)
    .map(({ check, mark, color }) => `${theme.fg(color, mark)} ${check}`)
    .join('  ')
