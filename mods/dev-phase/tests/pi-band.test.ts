import { expect, test } from 'claude-code/testing'

import { UNCHECKED } from '../core/checklist'
import { bandLine } from '../pi/band'
import type { BandTheme } from '../pi/band'

const theme: BandTheme = { fg: (color, text) => `<${color}>${text}` }

test('a fresh session shows all three checks crossed on one line', () => {
  expect(bandLine(theme, UNCHECKED)).toBe('<error>✗ code-review  <error>✗ qa  <error>✗ qa-tour')
})

test('a set check is drawn as a green tick', () => {
  expect(bandLine(theme, { ...UNCHECKED, qa: true })).toBe('<error>✗ code-review  <success>✓ qa  <error>✗ qa-tour')
})
