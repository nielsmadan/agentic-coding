import { expect, test } from 'claude-code/testing'

import { UNCHECKED } from '../core/checklist'
import { bandLine } from '../pi/band'
import type { BandTheme } from '../pi/band'

const theme: BandTheme = { fg: (color, text) => `<${color}>${text}` }

test('a fresh session shows every check crossed on one line', () => {
  expect(bandLine(theme, UNCHECKED)).toBe('<error>✗ code-review  <error>✗ fixes-made  <error>✗ qa  <error>✗ qa-tour')
})

test('a set check is drawn as a green tick', () => {
  expect(bandLine(theme, { ...UNCHECKED, qa: true })).toBe('<error>✗ code-review  <error>✗ fixes-made  <success>✓ qa  <error>✗ qa-tour')
})

test('a note follows the band dimmed, cut to the width left, and is dropped when too little is left', () => {
  const note = { checks: ['qa'] as const, reason: 'error-state rework', at: 1 }
  expect(bandLine(theme, UNCHECKED, note, 100)).toBe(
    '<error>✗ code-review  <error>✗ fixes-made  <error>✗ qa  <error>✗ qa-tour  <dim>↺ qa: error-state rework',
  )
  expect(bandLine(theme, UNCHECKED, note, 62)).toBe(
    '<error>✗ code-review  <error>✗ fixes-made  <error>✗ qa  <error>✗ qa-tour  <dim>↺ qa: error-sta…',
  )
  expect(bandLine(theme, UNCHECKED, note, 57)).toBe(
    '<error>✗ code-review  <error>✗ fixes-made  <error>✗ qa  <error>✗ qa-tour',
  )
})
