import { describe, expect, test } from 'claude-code/testing'

import { digest } from '../core/phase'
import {
  hasHistory,
  lastAssistantStop,
  latestState,
  latestTitle,
  skillFromCommand,
  skillFromUserMessage,
  skillResolver,
  toDigestMessages,
} from '../pi/transcript'
import type { PiEntry } from '../pi/transcript'

const skillOf = skillResolver(
  [
    { name: 'skill:commit', source: 'skill', sourceInfo: { path: '/u/.pi/agent/skills/commit/SKILL.md' } },
    { name: 'skill:code-review', source: 'skill', sourceInfo: { path: '/u/.pi/agent/skills/code-review/SKILL.md' } },
    { name: 'skill:fake', source: 'extension', sourceInfo: { path: '/u/.pi/agent/extensions/fake/SKILL.md' } },
  ],
  { cwd: '/u/w', home: '/u' },
)

const message = (value: Record<string, unknown>): PiEntry => ({ type: 'message', message: value })

const saved = (data: unknown): PiEntry => ({ type: 'custom', customType: 'dev-phase', data })

const EXPANDED = '<skill name="commit" location="/s/SKILL.md">\nReferences are relative to /s.\n\nbody\n</skill>\n\nfix it'

describe('skillResolver', () => {
  test('a registered SKILL.md names its skill from an absolute path', () => {
    expect(skillOf('/u/.pi/agent/skills/commit/SKILL.md')).toBe('commit')
  })

  test('home, @ and relative paths resolve against the working directory', () => {
    expect(skillOf('~/.pi/agent/skills/commit/SKILL.md')).toBe('commit')
    expect(skillOf('@../.pi/./agent//skills/code-review/SKILL.md')).toBe('code-review')
  })

  test('a SKILL.md that is not a registered skill names nothing', () => {
    expect(skillOf('/u/ac/loadout/skills/commit/SKILL.md')).toBeUndefined()
  })

  test('a command named skill: that is not a skill names nothing', () => {
    expect(skillOf('/u/.pi/agent/extensions/fake/SKILL.md')).toBeUndefined()
  })

  test('a bare ~ resolves to home', () => {
    const atHome = skillResolver([{ name: 'skill:home', source: 'skill', sourceInfo: { path: '/u' } }], {
      cwd: '/u/w',
      home: '/u',
    })
    expect(atHome('~')).toBe('home')
  })
})

describe('skillFromCommand', () => {
  test('a reader command names the skill it reads, quoted or not', () => {
    expect(skillFromCommand('sed -n 1,80p "~/.pi/agent/skills/commit/SKILL.md"', skillOf)).toBe('commit')
  })

  test('shell punctuation around the path does not hide it', () => {
    expect(skillFromCommand('cat ~/.pi/agent/skills/commit/SKILL.md;', skillOf)).toBe('commit')
    expect(skillFromCommand('cat ~/.pi/agent/skills/commit/SKILL.md|head -5', skillOf)).toBe('commit')
    expect(skillFromCommand('cd /u && (cat ~/.pi/agent/skills/code-review/SKILL.md)', skillOf)).toBe('code-review')
  })

  test('a command that only mentions the file is not a skill load', () => {
    expect(skillFromCommand('grep foo ~/.pi/agent/skills/commit/SKILL.md', skillOf)).toBeUndefined()
  })
})

describe('skillFromUserMessage', () => {
  test('an expanded /skill: message names its skill', () => {
    expect(skillFromUserMessage({ role: 'user', content: EXPANDED })).toBe('commit')
    expect(skillFromUserMessage({ role: 'user', content: [{ type: 'text', text: EXPANDED }] })).toBe('commit')
  })

  test('plain user text names no skill', () => {
    expect(skillFromUserMessage({ role: 'user', content: '/skill:commit' })).toBeUndefined()
  })
})

describe('toDigestMessages', () => {
  test('a /skill: expansion becomes a Skill call carrying only its arguments as text', () => {
    expect(toDigestMessages([message({ role: 'user', content: EXPANDED })], skillOf)).toEqual([
      { role: 'user', text: 'fix it', toolUses: [{ tool: 'Skill', input: { skill: 'commit' } }] },
    ])
  })

  test('an unterminated skill block stays plain text', () => {
    const text = '<skill name="commit" location="/s/SKILL.md">\nbody'
    expect(toDigestMessages([message({ role: 'user', content: text })], skillOf)).toEqual([
      { role: 'user', text, toolUses: [] },
    ])
  })

  test('assistant tool calls, skill reads and nested codemode calls are listed in order under canonical names', () => {
    const entries = [
      message({
        role: 'assistant',
        content: [
          { type: 'thinking', thinking: 'hmm' },
          { type: 'text', text: 'Committing.' },
          { type: 'toolCall', id: 'c1', name: 'read', arguments: { path: '~/.pi/agent/skills/commit/SKILL.md' } },
          { type: 'toolCall', id: 'c2', name: 'codemode', arguments: { code: '...' } },
        ],
        stopReason: 'toolUse',
      }),
      message({
        role: 'toolResult',
        toolCallId: 'c2',
        toolName: 'codemode',
        content: [],
        nestedCalls: { calls: [{ id: 'c2/1', name: 'bash', arguments: { command: 'git commit -m "x"' } }], complete: true },
      }),
      message({ role: 'bashExecution', command: 'npm test', output: '' }),
    ]
    const messages = toDigestMessages(entries, skillOf)
    expect(messages).toEqual([
      {
        role: 'assistant',
        text: 'Committing.',
        toolUses: [
          { tool: 'Skill', input: { skill: 'commit' } },
          { tool: 'Codemode', input: { code: '...' } },
          { tool: 'Bash', input: { command: 'git commit -m "x"' } },
        ],
      },
      { role: 'user', text: '', toolUses: [{ tool: 'Bash', input: { command: 'npm test' } }] },
    ])
    expect(digest(messages)).toBe(
      'assistant: Committing. [Skill(commit), Codemode, Bash(git commit -m "x")]\nuser:  [Bash(npm test)]',
    )
  })

  test('a !! command kept out of the model context is kept out of the digest', () => {
    const entries = [
      message({ role: 'bashExecution', command: 'cat .env', output: '', excludeFromContext: true }),
      message({ role: 'user', content: 'hi' }),
    ]
    expect(toDigestMessages(entries, skillOf)).toEqual([{ role: 'user', text: 'hi', toolUses: [] }])
  })
})

describe('saved state', () => {
  const record = { phase: 'planning', at: 1, source: 'skill' }

  test('the last valid dev-phase entry wins over invalid and foreign ones', () => {
    const entries = [
      saved({ record, topic: null }),
      saved({ record: { phase: 'bogus', at: 1, source: 'skill' }, topic: null }),
      saved({ record, topic: { bogus: 1 } }),
      { type: 'custom', customType: 'other', data: { record: null, topic: null } },
    ]
    expect(latestState(entries)).toEqual({ record, topic: null })
  })

  test('a stored none is kept as a decision', () => {
    expect(latestState([saved({ record, topic: null }), saved({ record: null, topic: null })])).toEqual({
      record: null,
      topic: null,
    })
  })

  test('a branch without a dev-phase entry has no saved state', () => {
    expect(latestState([message({ role: 'user', content: 'hi' })])).toBeUndefined()
  })

  test('the last title the mod gave survives a later entry without a topic', () => {
    const titled = { name: 'login bug', at: 1, titled: 'login bug' }
    expect(latestTitle([saved({ record, topic: titled }), saved({ record: null, topic: null })])).toBe('login bug')
  })

  test('history means a user or assistant message', () => {
    expect(hasHistory([message({ role: 'user', content: 'hi' })])).toBe(true)
    expect(hasHistory([message({ role: 'bashExecution', command: 'ls' }), saved({ record, topic: null })])).toBe(
      false,
    )
  })

  test('the stop reason comes from the last assistant message', () => {
    const messages = [
      { role: 'assistant', stopReason: 'toolUse' },
      { role: 'assistant', stopReason: 'stop' },
      { role: 'toolResult' },
    ]
    expect(lastAssistantStop(messages)).toBe('stop')
  })
})
