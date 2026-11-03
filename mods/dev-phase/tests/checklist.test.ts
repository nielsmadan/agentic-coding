import { describe, expect, test } from 'claude-code/testing'

import {
  asChecks,
  asStoredChecks,
  checkItems,
  digest,
  digestPrompt,
  forkPrompt,
  isCheckRun,
  isGitCommit,
  parseFeature,
  parseStale,
  redact,
  retitle,
  skillEffect,
  staleKeys,
  UNCHECKED,
  unearnedChecks,
  unknownStale,
  verdictState,
  withCheck,
  withoutChecks,
} from '../core/checklist'

const ALL = { 'code-review': true, qa: true, 'qa-tour': true }

describe('skillEffect', () => {
  test('the three checklist skills set their own check and dirty the turn, under a plugin prefix too', () => {
    expect(skillEffect('code-review')).toEqual({ check: 'code-review', isDirtying: true })
    expect(skillEffect('qa')).toEqual({ check: 'qa', isDirtying: true })
    expect(skillEffect('qa-tour')).toEqual({ check: 'qa-tour', isDirtying: true })
    expect(skillEffect('local:qa')).toEqual({ check: 'qa', isDirtying: true })
  })

  test('planning skills dirty the turn without a check, under a plugin prefix too', () => {
    expect(skillEffect('plan')).toEqual({ check: undefined, isDirtying: true })
    expect(skillEffect('superpowers:brainstorming')).toEqual({ check: undefined, isDirtying: true })
  })

  test('other skills, review and test ones included, do neither', () => {
    expect(skillEffect('review-correctness')).toEqual({ check: undefined, isDirtying: false })
    expect(skillEffect('test')).toEqual({ check: undefined, isDirtying: false })
    expect(skillEffect('commit')).toEqual({ check: undefined, isDirtying: false })
  })
})

describe('checks', () => {
  test('the band lists every check in order with its mark and colour', () => {
    expect(checkItems({ ...UNCHECKED, qa: true })).toEqual([
      { check: 'code-review', mark: '✗', color: 'error' },
      { check: 'qa', mark: '✓', color: 'success' },
      { check: 'qa-tour', mark: '✗', color: 'error' },
    ])
  })

  test('setting a check leaves the others as they were', () => {
    expect(withCheck({ ...UNCHECKED, qa: true }, 'code-review')).toEqual({ 'code-review': true, qa: true, 'qa-tour': false })
  })

  test('cleared checks are crossed and the rest kept', () => {
    expect(withoutChecks(ALL, ['qa'])).toEqual({ 'code-review': true, qa: false, 'qa-tour': true })
    expect(withoutChecks(UNCHECKED, [])).toEqual(UNCHECKED)
  })

  test('only a record with all three booleans is read back, as a fresh record of just those', () => {
    expect(asChecks({ ...ALL, extra: 1 })).toEqual(ALL)
    expect(asChecks({ 'code-review': true, qa: 'yes', 'qa-tour': false })).toBeUndefined()
  })

  test('a stored phase record from before the checklist reads as every check crossed', () => {
    expect(asStoredChecks({ phase: 'code review', at: 1, source: 'skill' })).toEqual(UNCHECKED)
    expect(asStoredChecks(null)).toEqual(UNCHECKED)
    expect(asStoredChecks(ALL)).toEqual(ALL)
    expect(asStoredChecks('garbage')).toBeUndefined()
  })

  test('a run that is not answered takes back only the checks it newly set', () => {
    expect(unearnedChecks(new Map([['qa', false], ['code-review', true]]))).toEqual(['qa'])
  })
})

describe('parseStale', () => {
  test('reads check names in any case and spelling', () => {
    expect(parseStale('FEATURE: x\nSTALE: QA, Code Review')).toEqual(['code-review', 'qa'])
    expect(parseStale('STALE: qa_tour and qa.')).toEqual(['qa', 'qa-tour'])
    expect(parseStale('stale: "code-review"')).toEqual(['code-review'])
  })

  test('reads markdown, bullets and explanations around the names', () => {
    expect(parseStale('**STALE:** qa')).toEqual(['qa'])
    expect(parseStale('- STALE: `qa-tour` (moved on)')).toEqual(['qa-tour'])
  })

  test('all means every check', () => {
    expect(parseStale('STALE: all')).toEqual(['code-review', 'qa', 'qa-tour'])
    expect(parseStale('STALE: all three')).toEqual(['code-review', 'qa', 'qa-tour'])
  })

  test('only a line that starts with the label counts, and the last one wins', () => {
    expect(parseStale('Not stale: code-review\nSTALE: qa')).toEqual(['qa'])
    expect(parseStale('STALE: qa\nSTALE: none')).toEqual([])
  })

  test('none and unknown names cross nothing, and unknown names are reported', () => {
    expect(parseStale('STALE: none')).toEqual([])
    expect(parseStale('STALE: security-review, qa')).toEqual(['qa'])
    expect(unknownStale('STALE: security-review, qa, none')).toEqual(['security-review'])
  })

  test('an answer without a stale line has no stale verdict', () => {
    expect(parseStale('FEATURE: x')).toBeUndefined()
  })
})

describe('parseFeature', () => {
  test('reads the feature line without quotes or markdown', () => {
    expect(parseFeature('FEATURE: "dev-phase mod".\nSTALE: none')).toBe('dev-phase mod')
    expect(parseFeature('**FEATURE:** csv export')).toBe('csv export')
    expect(parseFeature('FEATURE: none\nSTALE: none')).toBeNull()
    expect(parseFeature('STALE: none')).toBeUndefined()
  })
})

describe('verdictState', () => {
  const current = { checks: ALL, topic: { name: 'csv export', at: 1 } }

  test('a verdict crosses the stale checks and keeps an unchanged feature', () => {
    expect(verdictState('FEATURE: csv export\nSTALE: qa', current, 9)).toEqual({
      checks: { 'code-review': true, qa: false, 'qa-tour': true },
      topic: current.topic,
    })
  })

  test('a new feature is named with the time it was named', () => {
    expect(verdictState('FEATURE: login bug\nSTALE: code-review, qa, qa-tour', current, 9)).toEqual({
      checks: UNCHECKED,
      topic: { name: 'login bug', at: 9 },
    })
  })

  test('a check held for the turn that ran it survives a stale verdict', () => {
    expect(verdictState('STALE: code-review, qa', current, 9, ['code-review'])?.checks).toEqual({
      'code-review': true,
      qa: false,
      'qa-tour': true,
    })
  })

  test('a verdict missing a line keeps that part', () => {
    expect(verdictState('FEATURE: login bug', current, 9)?.checks).toBe(ALL)
    expect(verdictState('STALE: qa', current, 9)?.topic).toBe(current.topic)
  })

  test('an answer with neither line is unparseable', () => {
    expect(verdictState('I would say we are reviewing.', current, 9)).toBeUndefined()
  })
})

describe('retitle', () => {
  test('titles an untitled session or one still carrying the mod title', () => {
    expect(retitle({ name: 'login bug', at: 1 }, undefined)).toBe('login bug')
    expect(retitle({ name: 'login bug', at: 1, titled: 'old mod' }, 'old mod')).toBe('login bug')
  })

  test('leaves a title the user chose', () => {
    expect(retitle({ name: 'login bug', at: 1, titled: 'old mod' }, 'my title')).toBeUndefined()
  })
})

describe('prompts', () => {
  test('the fork is told the current feature name so it keeps it', () => {
    expect(forkPrompt({ checks: UNCHECKED, topic: { name: 'dev-phase mod', at: 1 } }, 'Done.')).toContain(
      'currently named "dev-phase mod"',
    )
  })

  test('the fork is told which checks are set and asked for both lines', () => {
    const prompt = forkPrompt({ checks: { ...UNCHECKED, qa: true, 'qa-tour': true }, topic: null }, 'Done.')
    expect(prompt).toContain('Set now: qa, qa-tour.')
    expect(prompt).toContain('FEATURE: <name|none>\nSTALE: <')
  })

  test('the digest prompt says when no check is set', () => {
    expect(digestPrompt({ checks: UNCHECKED, topic: null }, 'user: hi')).toContain('Set now: none.')
  })

  test('the digest prompt says a run older than the excerpt came before every change shown', () => {
    expect(digestPrompt({ checks: ALL, topic: null }, 'user: hi')).toContain(
      'ran before all of it, so every change shown came after that run',
    )
  })
})

test('command detectors recognise commits and check runs', () => {
  expect(isGitCommit('git -C /w commit -m "x"')).toBe(true)
  expect(isCheckRun('uv run pytest -q')).toBe(true)
  expect(isCheckRun('pnpm run typecheck')).toBe(true)
})

test('digest lists rows with their tool calls', () => {
  const rows = digest([
    { role: 'user', text: 'commit it', toolUses: [] },
    {
      role: 'assistant',
      text: 'Committing.',
      toolUses: [{ tool: 'Bash', input: { command: 'git commit -m "feat: x"' } }],
    },
  ])
  expect(rows).toBe('user: commit it\nassistant: Committing. [Bash(git commit -m "feat: x")]')
})

test('digest names the file an edit changed', () => {
  const rows = digest([
    {
      role: 'assistant',
      text: 'Fixed.',
      toolUses: [
        { tool: 'Edit', input: { file_path: '/w/src/a.ts', old_string: 'a', new_string: 'b' } },
        { tool: 'Write', input: { path: '/home/me/w/README.md', content: 'x' } },
        { tool: 'Read', input: { file_path: '/w/src/b.ts' } },
      ],
    },
  ])
  expect(rows).toBe('assistant: Fixed. [Edit(/w/src/a.ts), Write(~/w/README.md), Read]')
})

test('digest keeps the end of a long edited path, where the file name is', () => {
  const path = `/Users/me/${'deep/'.repeat(20)}InvoiceExportDialog.tsx`
  const row = digest([{ role: 'assistant', text: 'Fixed.', toolUses: [{ tool: 'Edit', input: { file_path: path } }] }])
  const shown = /Edit\((.*)\)/.exec(row)?.[1] ?? ''
  expect(shown).toHaveLength(80)
  expect(shown.startsWith('…')).toBe(true)
  expect(shown.endsWith('deep/InvoiceExportDialog.tsx')).toBe(true)
})

test('digest masks secrets in shell commands', () => {
  expect(redact('export OPENROUTER_API_KEY=sk-or-v1-abc123')).toBe('export OPENROUTER_API_KEY=***')
  expect(redact('curl -H "Authorization: Bearer ghp_abc123" x')).toBe('curl -H "Authorization: Bearer ***" x')
  expect(redact('gh auth login --with-token ghp_abc123')).toBe('gh auth login --with-token ***')
  expect(redact('mysql --password hunter2 db')).toBe('mysql --password *** db')
})

test('digest lists only the last tool calls of a busy row', () => {
  const toolUses = Array.from({ length: 15 }, (_, index) => ({ tool: `T${index}`, input: {} }))
  expect(digest([{ role: 'assistant', text: 'Busy.', toolUses }])).toBe(
    'assistant: Busy. [+3 more, T3, T4, T5, T6, T7, T8, T9, T10, T11, T12, T13, T14]',
  )
})

test('digest keeps the last message long enough to hold its hand-off', () => {
  const long = `${'x'.repeat(1000)} try it yourself`
  const rows = digest([
    { role: 'assistant', text: long, toolUses: [] },
    { role: 'assistant', text: long, toolUses: [] },
  ])
  expect(rows.split('\n')).toEqual([`assistant: ${'x'.repeat(300)}`, `assistant: ${long}`])
})

describe('staleKeys', () => {
  const keys = ['session:a', 'topic:a', 'session:b', 'session:c', 'topic:b', 'session:d']

  test('drops every key of the least recently written sessions', () => {
    expect(staleKeys(keys, 2, 'x')).toEqual(['session:a', 'topic:a', 'session:c'])
  })

  test('keeps the current session past the limit', () => {
    expect(staleKeys(keys, 2, 'a')).toEqual(['session:c'])
  })
})
