import { expect, test } from 'claude-code/testing'

import { bandLine } from '../pi/band'
import type { BandTheme } from '../pi/band'

const theme: BandTheme = {
  style: (text, { fg, bold, dim }) => `<${[fg, bold === true ? 'b' : '', dim === true ? 'd' : ''].join('')}>${text}`,
  fg: (color, text) => `<${color}>${text}`,
}

test('a session without a phase says so', () => {
  expect(bandLine(theme, null, null)).toBe('<dim>● no phase yet')
})

test('a session without a phase still names its feature', () => {
  expect(bandLine(theme, null, { name: 'CSV export', at: 1 })).toBe('<dim>● no phase yet<dim> · CSV export')
})

test('a phase is drawn bold in its colour, followed by the feature', () => {
  expect(bandLine(theme, { phase: 'code review', at: 1, source: 'skill' }, { name: 'CSV export', at: 1 })).toBe(
    '<mdLink>● <b>code review<dim> · CSV export',
  )
})

test('a provisional phase from an edit is drawn dim', () => {
  expect(bandLine(theme, { phase: 'implementation', at: 1, source: 'edit' }, null)).toBe(
    '<thinkingMaxd>● <bd>implementation',
  )
})
