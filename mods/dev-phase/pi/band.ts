import type { DevChecks, DevNote } from '../types'
import { checkItems, noteSpace, noteText } from '../core/checklist'
import type { CheckItem } from '../core/checklist'

export type PiColor = CheckItem['color'] | 'dim'

export type BandTheme = {
  fg(color: PiColor, text: string): string
}

export const bandLine = (theme: BandTheme, checks: DevChecks, note?: DevNote | null, width = Infinity): string => {
  const band = checkItems(checks)
    .map(({ check, mark, color }) => `${theme.fg(color, mark)} ${check}`)
    .join('  ')
  const text = noteText(note, noteSpace(width))
  return text === undefined ? band : `${band}  ${theme.fg('dim', text)}`
}
