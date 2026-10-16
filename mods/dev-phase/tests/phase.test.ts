import { describe, expect, test } from 'claude-code/testing'

import {
  digest,
  forkPrompt,
  isCheckRun,
  isGitCommit,
  parseFeature,
  parseVerdict,
  phaseOfSkill,
  provisionalPhase,
  redact,
  retitle,
  staleKeys,
} from '../core/phase'

describe('phaseOfSkill', () => {
  test('maps workflow skills to their phase', () => {
    expect(phaseOfSkill('commit', undefined)).toBe('wrap-up')
    expect(phaseOfSkill('superpowers:writing-plans', undefined)).toBe('planning')
    expect(phaseOfSkill('writing-plans', undefined)).toBe('planning')
    expect(phaseOfSkill('review-plan', undefined)).toBe('planning')
    expect(phaseOfSkill('review-security', undefined)).toBe('code review')
    expect(phaseOfSkill('review-todo', undefined)).toBe('review fixes')
    expect(phaseOfSkill('qa', undefined)).toBe('agent QA')
  })

  test('maps fixing skills to the fixes of the phase they interrupt', () => {
    expect(phaseOfSkill('hard-fix', 'agent QA')).toBe('QA fixes')
    expect(phaseOfSkill('superpowers:systematic-debugging', 'code review')).toBe('review fixes')
    expect(phaseOfSkill('pre-existing', 'planning')).toBe('implementation')
  })
})

describe('provisionalPhase', () => {
  test('an edit moves planning to implementation and QA or review to their fixes', () => {
    expect(provisionalPhase(undefined, '/w/a.ts')).toBe('implementation')
    expect(provisionalPhase('planning', '/w/a.ts')).toBe('implementation')
    expect(provisionalPhase('manual QA', '/w/a.ts')).toBe('QA fixes')
    expect(provisionalPhase('code review', '/w/a.ts')).toBe('review fixes')
  })

  test('a doc edit or an edit mid-implementation leaves the phase to the model', () => {
    expect(provisionalPhase('planning', '/w/plan.md')).toBeUndefined()
    expect(provisionalPhase('implementation', '/w/a.ts')).toBeUndefined()
  })
})

describe('parseFeature', () => {
  test('reads the feature line without quotes', () => {
    expect(parseFeature('PHASE: implementation\nFEATURE: "dev-phase mod".')).toBe('dev-phase mod')
    expect(parseFeature('PHASE: implementation\nFEATURE: none')).toBeNull()
    expect(parseFeature('PHASE: implementation')).toBeUndefined()
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

test('the fork is told the current feature name so it keeps it', () => {
  expect(forkPrompt(null, { name: 'dev-phase mod', at: 1 }, 'Done.')).toContain('currently named "dev-phase mod"')
})

describe('parseVerdict', () => {
  test('reads the phase line in any case and spelling', () => {
    expect(parseVerdict('PHASE: Code Review')).toBe('code review')
    expect(parseVerdict('Thinking it over.\nPHASE: wrap up')).toBe('wrap-up')
    expect(parseVerdict('PHASE: QA fixes')).toBe('QA fixes')
    expect(parseVerdict('PHASE: none')).toBeNull()
  })

  test('an answer without a phase line is unparseable', () => {
    expect(parseVerdict('I would say we are reviewing.')).toBeUndefined()
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
