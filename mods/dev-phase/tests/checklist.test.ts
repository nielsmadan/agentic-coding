import { describe, expect, test } from 'claude-code/testing'

import {
  asChecks,
  asNote,
  asStoredChecks,
  awaitsAddressing,
  checkItems,
  digest,
  digestPrompt,
  forkPrompt,
  isCheckRun,
  isGitCommit,
  noteSpace,
  noteText,
  parseAddressed,
  parseFeature,
  parseReason,
  parseStale,
  recordBefore,
  redact,
  restoreChecks,
  retitle,
  skillEffect,
  staleKeys,
  UNCHECKED,
  unknownStale,
  verdictState,
  withCheck,
  withoutChecks,
  withoutNoted,
} from '../core/checklist'

const ALL = { 'code-review': true, 'fixes-made': true, qa: true, 'qa-tour': true }
const REVIEWED = { ...UNCHECKED, 'code-review': true }
const ALL_REVIEW = { ...REVIEWED, 'fixes-made': true }

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

  test('fixes-made is no skill, so a skill of that name sets nothing', () => {
    expect(skillEffect('fixes-made')).toEqual({ check: undefined, isDirtying: false })
  })
})

describe('checks', () => {
  test('the band lists every check in order with its mark and colour', () => {
    expect(checkItems({ ...UNCHECKED, qa: true })).toEqual([
      { check: 'code-review', mark: '✗', color: 'error' },
      { check: 'fixes-made', mark: '✗', color: 'error' },
      { check: 'qa', mark: '✓', color: 'success' },
      { check: 'qa-tour', mark: '✗', color: 'error' },
    ])
  })

  test('setting a check leaves the others as they were', () => {
    expect(withCheck({ ...ALL, qa: false }, 'qa')).toEqual(ALL)
  })

  test('a code-review run brings new findings, so it crosses fixes-made', () => {
    expect(withCheck(ALL, 'code-review')).toEqual({ ...ALL, 'fixes-made': false })
  })

  test('cleared checks are crossed and the rest kept', () => {
    expect(withoutChecks(ALL, ['qa'])).toEqual({ ...ALL, qa: false })
    expect(withoutChecks(UNCHECKED, [])).toEqual(UNCHECKED)
  })

  test('fixes-made is crossed with code-review', () => {
    expect(withoutChecks(ALL, ['code-review'])).toEqual({ ...ALL, 'code-review': false, 'fixes-made': false })
  })

  test('only a reviewed session with fixes-made crossed awaits addressing', () => {
    expect(awaitsAddressing(REVIEWED)).toBe(true)
    expect(awaitsAddressing(ALL)).toBe(false)
    expect(awaitsAddressing(UNCHECKED)).toBe(false)
  })

  test('only a record with every skill check as a boolean is read back, as a fresh record of just the checks', () => {
    expect(asChecks({ ...ALL, extra: 1 })).toEqual(ALL)
    expect(asChecks({ 'code-review': true, qa: 'yes', 'qa-tour': false })).toBeUndefined()
  })

  test('a record from before fixes-made reads it as crossed', () => {
    expect(asChecks({ 'code-review': true, qa: true, 'qa-tour': false })).toEqual({ ...REVIEWED, qa: true })
  })

  test('a record stored under the old name findings-addressed keeps its tick', () => {
    expect(asChecks({ 'code-review': true, 'findings-addressed': true, qa: true, 'qa-tour': true })).toEqual(ALL)
  })

  test('a stored phase record from before the checklist reads as every check crossed', () => {
    expect(asStoredChecks({ phase: 'code review', at: 1, source: 'skill' })).toEqual(UNCHECKED)
    expect(asStoredChecks(null)).toEqual(UNCHECKED)
    expect(asStoredChecks(ALL)).toEqual(ALL)
    expect(asStoredChecks('garbage')).toBeUndefined()
  })

  test('a turn records each check its skills changed, as it was before the first change', () => {
    const first = recordBefore(new Map(), 'code-review', ALL, withCheck(ALL, 'code-review'))
    expect([...first]).toEqual([['code-review', true], ['fixes-made', true]])
    const second = recordBefore(first, 'qa', { ...ALL, 'fixes-made': false }, { ...ALL, 'fixes-made': false, qa: false })
    expect([...second]).toEqual([['code-review', true], ['fixes-made', true], ['qa', true]])
  })

  test('a run that is not answered puts back what its skills changed', () => {
    const before = new Map([['code-review', false], ['fixes-made', true]] as const)
    expect(restoreChecks({ ...ALL, 'fixes-made': false }, before)).toEqual({ ...ALL, 'code-review': false })
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

  test('fixes-made is not a stale choice, and all means the skill checks', () => {
    expect(parseStale('STALE: fixes-made')).toEqual([])
    expect(unknownStale('STALE: fixes-made')).toEqual(['fixes-made'])
    expect(parseStale('STALE: all')).toEqual(['code-review', 'qa', 'qa-tour'])
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

describe('parseAddressed', () => {
  test('reads yes or no in any case and markdown', () => {
    expect(parseAddressed('STALE: none\nADDRESSED: yes')).toBe(true)
    expect(parseAddressed('**ADDRESSED:** No.')).toBe(false)
    expect(parseAddressed('ADDRESSED: none')).toBeUndefined()
    expect(parseAddressed('STALE: none')).toBeUndefined()
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

  test('a verdict crosses the stale checks, keeps an unchanged feature and notes why', () => {
    expect(verdictState('FEATURE: csv export\nSTALE: qa\nREASON: retry loop rewrite', current, 9)).toEqual({
      checks: { ...ALL, qa: false },
      topic: current.topic,
      note: { checks: ['qa'], reason: 'retry loop rewrite', at: 9 },
    })
  })

  test('addressed findings tick fixes-made while code-review holds', () => {
    const reviewed = { checks: REVIEWED, topic: null }
    expect(verdictState('STALE: none\nADDRESSED: yes', reviewed, 9)?.checks).toEqual(ALL_REVIEW)
    expect(verdictState('STALE: code-review\nADDRESSED: yes', reviewed, 9)?.checks).toEqual(UNCHECKED)
    expect(verdictState('STALE: none\nADDRESSED: no', reviewed, 9)?.checks).toEqual(REVIEWED)
  })

  test('an answer of no never crosses findings already addressed', () => {
    expect(verdictState('STALE: none\nADDRESSED: no', current, 9)?.checks).toEqual(ALL)
  })

  test('a new feature is named with the time it was named', () => {
    expect(verdictState('FEATURE: login bug\nSTALE: code-review, qa, qa-tour', current, 9)).toEqual({
      checks: UNCHECKED,
      topic: { name: 'login bug', at: 9 },
      note: { checks: ['code-review', 'qa', 'qa-tour'], reason: 'changes since', at: 9 },
    })
  })

  test('a check held for the turn that ran it survives a stale verdict', () => {
    expect(verdictState('STALE: code-review, qa', current, 9, ['code-review'])?.checks).toEqual({ ...ALL, qa: false })
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

  test('both prompts ask for a name for work that is not software', () => {
    expect(forkPrompt({ checks: UNCHECKED, topic: null }, 'Done.')).toContain('including writing, research or planning')
    expect(digestPrompt({ checks: UNCHECKED, topic: null }, 'user: hi')).toContain('Answer none only when the session has not started on any task yet.')
  })

  test('the fork is told which checks are set and asked for both lines', () => {
    const prompt = forkPrompt({ checks: { ...UNCHECKED, qa: true, 'qa-tour': true }, topic: null }, 'Done.')
    expect(prompt).toContain('Set now: qa, qa-tour.')
    expect(prompt).toContain('FEATURE: <name|none>\nSTALE: <')
  })

  test('only a review whose findings are open asks whether they were addressed', () => {
    expect(forkPrompt({ checks: REVIEWED, topic: null }, 'Done.')).toContain('Answer with exactly four lines')
    expect(forkPrompt({ checks: REVIEWED, topic: null }, 'Done.')).toContain('otherwise none>\nADDRESSED: <yes|no>')
    expect(digestPrompt({ checks: REVIEWED, topic: null }, 'user: hi')).toContain('Addressed: whether every finding')
    expect(forkPrompt({ checks: ALL, topic: null }, 'Done.')).toContain('Answer with exactly three lines')
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

describe('note', () => {
  const note = { checks: ['code-review', 'qa'] as const, reason: 'error-state rework', at: 9 }
  const current = { checks: ALL, topic: null }

  test('the note names the reset checks and why, cut to the space it gets', () => {
    expect(noteText(note, 40)).toBe('↺ code-review, qa: error-state rework')
    expect(noteText(note, 15)).toBe('↺ code-review,…')
    expect(noteText(note, 11)).toBeUndefined()
    expect(noteText(null, 40)).toBeUndefined()
  })

  test('the note gets the columns the band and its gap leave', () => {
    expect(noteSpace(80)).toBe(34)
  })

  test('running a noted check again takes it out of the note, which goes once none is left', () => {
    expect(withoutNoted(note, 'qa')).toEqual({ ...note, checks: ['code-review'] })
    expect(withoutNoted({ ...note, checks: ['qa'] }, 'qa')).toBeNull()
    expect(withoutNoted(note, 'qa-tour')).toBe(note)
  })

  test('a verdict that resets nothing keeps the last note, and one that resets replaces it', () => {
    const noted = { ...current, note }
    expect(verdictState('STALE: none', noted, 20)?.note).toBe(note)
    expect(verdictState('STALE: qa-tour\nREASON: moved to login bug', noted, 20)?.note).toEqual({
      checks: ['qa-tour'],
      reason: 'moved to login bug',
      at: 20,
    })
  })

  test('the note lists only the checks the verdict actually crossed', () => {
    expect(verdictState('STALE: code-review, qa\nREASON: retry rewrite', current, 9, ['code-review'])?.note).toEqual({
      checks: ['qa'],
      reason: 'retry rewrite',
      at: 9,
    })
    expect(verdictState('STALE: qa\nREASON: x', { checks: UNCHECKED, topic: null }, 9)?.note).toBeUndefined()
  })

  test('parseReason trims markup, reads none as no reason and caps the length', () => {
    expect(parseReason('STALE: qa\nREASON: **error-state rework**.')).toBe('error-state rework')
    expect(parseReason('REASON: none')).toBeUndefined()
    expect(parseReason('STALE: qa')).toBeUndefined()
    expect(parseReason(`REASON: ${'x'.repeat(60)}`)).toBe('x'.repeat(40))
  })

  test('a stored note keeps only known checks', () => {
    expect(asNote({ checks: ['qa', 'lint'], reason: 'r', at: 1 })).toEqual({ checks: ['qa'], reason: 'r', at: 1 })
    expect(asNote({ checks: ['lint'], reason: 'r', at: 1 })).toBeUndefined()
    expect(asNote({ checks: ['qa'], reason: 3, at: 1 })).toBeUndefined()
  })
})

describe('staleKeys', () => {
  const keys = ['session:a', 'topic:a', 'session:b', 'session:c', 'topic:b', 'session:d']

  test('drops every key of the least recently written sessions', () => {
    expect(staleKeys(keys, 2, 'x')).toEqual(['session:a', 'topic:a', 'session:c'])
  })

  test('keeps the current session past the limit', () => {
    expect(staleKeys(keys, 2, 'a')).toEqual(['session:c'])
  })

  test('drops the note of a pruned session with its checks', () => {
    expect(staleKeys(['session:a', 'note:a', 'session:b'], 1, 'x')).toEqual(['session:a', 'note:a'])
  })
})
