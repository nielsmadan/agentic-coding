import type { On, SessionMessage } from 'claude-code'
import { expect, mock, test } from 'claude-code/testing'
import type { Engine } from 'claude-code/testing'

import { IDLE_MS as IDLE, UNCHECKED as NONE } from '../core/checklist'

const SURFACES = ['terminal', 'desktop'] as const

const BAND = {
  plugin: 'dev-phase',
  component: 'AbovePrompt',
  props: {
    hasSurvey: false,
    isWorking: false,
    maxRows: 6,
    bodyColumns: 76,
    scroll: { offset: 0, bodyRows: 5 },
    view: {},
  },
} as const

const USAGE = { input_tokens: 0, output_tokens: 0, cache_creation_input_tokens: 0, cache_read_input_tokens: 0 }

const TURN = { answer: 'Done.', durationMs: 1000, isAborted: false, turnId: 't1', reason: 'answer' } as const

const START = { cwd: '/w', surface: 'terminal', isInteractive: true } as const

const EDIT = { tool: 'Edit', file_path: '/w/a.ts', old_string: 'a', new_string: 'b' } as const

const ALL = { 'code-review': true, qa: true, 'qa-tour': true }

const CROSSED = '✗ code-review  ✗ qa  ✗ qa-tour'

type World = {
  store?: Record<string, unknown>
  turns?: number
  messages?: SessionMessage[]
  fork?: (prompt: string) => unknown
  complete?: (model: string, prompt: string) => unknown
  toolCall?: () => unknown
  promptTitle?: string
}

const answered = (text: string) => ({ isAnswered: true, text, usage: USAGE })

const unanswered = (reason: string) => ({ isAnswered: false, reason, status: 529, error: 'overloaded_error', usage: USAGE })

function engine(on: On, world: World = {}) {
  mock.store(on, world.store ?? {})
  const clock = mock.clock(on)
  on('session.id', () => ({ value: 'sess-1' }))
  on('session.turns', () => ({ value: world.turns ?? 0 }))
  on('session.messages', () => ({ value: world.messages ?? [] }))
  on('ui.log', () => ({ value: undefined }))
  on('model.fork', async ($, e) => ({
    value: (await (world.fork ?? (() => answered('FEATURE: none\nSTALE: none')))(e.prompt)) as never,
  }))
  on('model.complete', async ($, e) => ({
    value: (await (world.complete ?? (() => answered('FEATURE: none\nSTALE: none')))(e.model, e.prompt)) as never,
  }))
  on('session.start', ($, e) => ({ cwd: e.cwd }))
  on('turn.start', ($, e) => ({ turnId: e.turnId }))
  on('skill.prompt', ($, e) => ({ text: e.text }))
  on('turn.complete', ($, e) => ({ text: e.answer }))
  on('classic.SessionStart', () => ({}))
  on('classic.UserPromptSubmit', () => (world.promptTitle === undefined ? {} : { sessionTitle: world.promptTitle }))
  on('tool.call', () => (world.toolCall?.() ?? { result: {}, text: 'ok' }) as never)
  return clock
}

function recorder(answers: readonly unknown[]) {
  const prompts: string[] = []
  const reply = (prompt: string) => {
    prompts.push(prompt)
    return answers[Math.min(prompts.length, answers.length) - 1]
  }
  return { prompts, reply }
}

function gate() {
  let open: () => void = () => undefined
  const opened = new Promise<void>(resolve => {
    open = resolve
  })
  return { opened, open }
}

async function rows($: Engine, surface: (typeof SURFACES)[number] = 'terminal'): Promise<string> {
  const ui = await $.ui.mount({ ...BAND, surface })
  const found = await ui.findAll({ type: 'Text' })
  await ui.unmount()
  const texts = found.map(element => element.text)
  return texts
    .flatMap((text, index) => (index % 2 === 0 ? [`${text}${texts[index + 1] ?? ''}`] : []))
    .join('  ')
}

async function expectBand($: Engine, band: string): Promise<void> {
  for (const surface of SURFACES) expect(await rows($, surface)).toBe(band)
}

async function settle(clock: { advance: (ms: number) => Promise<void> }): Promise<void> {
  await clock.advance(1)
  await clock.advance(1)
}
test('a fresh session shows every check crossed on one line', async ($, on) => {
  engine(on)
  await $.session.start(START)
  await expectBand($, CROSSED)
  const ui = await $.ui.mount({ ...BAND, surface: 'terminal' })
  const marks = await ui.findAll({ type: 'Text', text: /✗/ })
  expect(marks.map(element => element.props.color)).toEqual(['error', 'error', 'error'])
  await ui.unmount()
})

test('a checklist skill ticks its check in green and keeps it across a resume', async ($, on) => {
  engine(on)
  await $.session.start(START)
  await $.skill.prompt({ skill: 'qa', text: 'qa' })
  await expectBand($, '✗ code-review  ✓ qa  ✗ qa-tour')
  const ui = await $.ui.mount({ ...BAND, surface: 'terminal' })
  expect((await ui.find({ type: 'Text', text: /✓/ }))?.props.color).toBe('success')
  await ui.unmount()
  await $.classic.SessionStart({ source: 'clear', session_id: 'sess-2' })
  await $.classic.SessionStart({ source: 'resume', session_id: 'sess-1' })
  await expectBand($, '✗ code-review  ✓ qa  ✗ qa-tour')
})

test('each checklist skill ticks only its own check', async ($, on) => {
  engine(on)
  await $.skill.prompt({ skill: 'qa-tour', text: 'tour' })
  await $.skill.prompt({ skill: 'code-review', text: 'review' })
  await expectBand($, '✓ code-review  ✗ qa  ✓ qa-tour')
})

test('a skill a subagent runs ticks nothing and asks nothing', async ($, on) => {
  const held = gate()
  const fork = recorder([answered('FEATURE: x\nSTALE: none')])
  const clock = engine(on, { fork: fork.reply, toolCall: () => held.opened.then(() => ({ result: {}, text: 'ok' })) })
  await $.session.start(START)
  const subagentSkill = { tool: 'Skill', skill: 'code-review', agentId: 'sub-1' } as const
  const call = $.tool.call(subagentSkill)
  await $.skill.prompt({ skill: 'code-review', text: 'review' })
  held.open()
  await call
  await expectBand($, CROSSED)
  await $.turn.complete(TURN)
  await clock.advance(IDLE)
  expect(fork.prompts).toEqual([])
})

test('after a subagent finishes a skill, the main agent running it ticks it', async ($, on) => {
  engine(on)
  await $.session.start(START)
  const subagentSkill = { tool: 'Skill', skill: 'plugin:code-review', agentId: 'sub-1' } as const
  await $.tool.call(subagentSkill)
  await $.skill.prompt({ skill: 'code-review', text: 'review' })
  await expectBand($, '✓ code-review  ✗ qa  ✗ qa-tour')
})

test('a skill the main agent runs through the Skill tool ticks its check', async ($, on) => {
  const held = gate()
  engine(on, { toolCall: () => held.opened.then(() => ({ result: {}, text: 'ok' })) })
  await $.session.start(START)
  const mainSkill = { tool: 'Skill', skill: 'qa' } as const
  const call = $.tool.call(mainSkill)
  await $.skill.prompt({ skill: 'qa', text: 'qa' })
  held.open()
  await call
  await expectBand($, '✗ code-review  ✓ qa  ✗ qa-tour')
})

test('an interrupted turn takes back the checks its skills newly set', async ($, on) => {
  engine(on, { store: { 'session:sess-1': { ...NONE, 'code-review': true } } })
  await $.session.start(START)
  await $.skill.prompt({ skill: 'code-review', text: 'review' })
  await $.skill.prompt({ skill: 'qa', text: 'qa' })
  await expectBand($, '✓ code-review  ✓ qa  ✗ qa-tour')
  await $.turn.complete({ ...TURN, reason: 'aborted', isAborted: true })
  await expectBand($, '✓ code-review  ✗ qa  ✗ qa-tour')
})

test("a verdict cannot cross a check its own turn ran, but crosses older ones", async ($, on) => {
  const fork = recorder([answered('FEATURE: x\nSTALE: code-review, qa')])
  const clock = engine(on, { store: { 'session:sess-1': { ...NONE, qa: true } }, fork: fork.reply })
  await $.session.start(START)
  await $.skill.prompt({ skill: 'code-review', text: 'review' })
  await $.tool.call(EDIT)
  await $.turn.complete(TURN)
  await clock.advance(IDLE)
  expect(fork.prompts).toHaveLength(1)
  await expectBand($, '✓ code-review  ✗ qa  ✗ qa-tour')
})

test('an idle session after an edit asks the fork, crosses what went stale and names the feature', async ($, on) => {
  const fork = recorder([answered('FEATURE: dev-phase mod\nSTALE: qa')])
  const clock = engine(on, { store: { 'session:sess-1': ALL }, fork: fork.reply })
  await $.session.start(START)
  await $.tool.call(EDIT)
  await $.turn.complete(TURN)
  await clock.advance(IDLE - 1)
  expect(fork.prompts).toEqual([])
  await clock.advance(1)
  expect(fork.prompts).toEqual([expect.stringContaining('Set now: code-review, qa, qa-tour.')])
  await expectBand($, '✓ code-review  ✗ qa  ✓ qa-tour')
  const result = await $.classic.UserPromptSubmit({ prompt: 'go', session_id: 'sess-1' })
  expect(result.sessionTitle).toBe('dev-phase mod')
})

test('a verdict that nothing went stale keeps every check', async ($, on) => {
  const clock = engine(on, { store: { 'session:sess-1': ALL }, fork: () => answered('FEATURE: x\nSTALE: none') })
  await $.session.start(START)
  await $.tool.call(EDIT)
  await $.turn.complete(TURN)
  await clock.advance(IDLE)
  await expectBand($, '✓ code-review  ✓ qa  ✓ qa-tour')
})

test('a planning skill asks the fork after its turn, which can start a new feature', async ($, on) => {
  const fork = recorder([answered('FEATURE: login bug\nSTALE: code-review, qa, qa-tour')])
  const clock = engine(on, { store: { 'session:sess-1': ALL }, fork: fork.reply })
  await $.session.start(START)
  await $.skill.prompt({ skill: 'plan', text: 'plan the login fix' })
  await $.turn.complete(TURN)
  await clock.advance(IDLE)
  expect(fork.prompts).toHaveLength(1)
  await expectBand($, CROSSED)
  const result = await $.classic.UserPromptSubmit({ prompt: 'go', session_id: 'sess-1' })
  expect(result.sessionTitle).toBe('login bug')
})

test('a checklist skill turn asks the fork so earlier checks are judged again', async ($, on) => {
  const fork = recorder([answered('FEATURE: x\nSTALE: qa')])
  const clock = engine(on, { store: { 'session:sess-1': { ...NONE, qa: true } }, fork: fork.reply })
  await $.session.start(START)
  await $.skill.prompt({ skill: 'code-review', text: 'review' })
  await $.turn.complete(TURN)
  await clock.advance(IDLE)
  expect(fork.prompts).toEqual([expect.stringContaining('Set now: code-review, qa.')])
  await expectBand($, '✓ code-review  ✗ qa  ✗ qa-tour')
})

test('a turn with another skill and no edits asks nothing', async ($, on) => {
  const fork = recorder([answered('FEATURE: x\nSTALE: none')])
  const clock = engine(on, { fork: fork.reply })
  await $.skill.prompt({ skill: 'status', text: 'status' })
  await $.turn.complete(TURN)
  await clock.advance(IDLE)
  expect(fork.prompts).toEqual([])
})

test('a reply before the idle wait moves the question to the next turn', async ($, on) => {
  const fork = recorder([answered('FEATURE: x\nSTALE: qa')])
  const clock = engine(on, { store: { 'session:sess-1': ALL }, fork: fork.reply })
  await $.session.start(START)
  await $.tool.call(EDIT)
  await $.turn.complete(TURN)
  await $.turn.start({ text: 'next', turnId: 't2' })
  await clock.advance(IDLE)
  expect(fork.prompts).toEqual([])
  await $.turn.complete({ ...TURN, turnId: 't2' })
  await clock.advance(IDLE)
  expect(fork.prompts).toHaveLength(1)
  await expectBand($, '✓ code-review  ✗ qa  ✓ qa-tour')
})

test('an unanswered fork is asked again after the next turn', async ($, on) => {
  const fork = recorder([unanswered('api-error'), answered('FEATURE: x\nSTALE: code-review')])
  const clock = engine(on, { store: { 'session:sess-1': ALL }, fork: fork.reply })
  await $.session.start(START)
  await $.tool.call({ tool: 'Bash', command: 'git commit -m x' })
  await $.turn.complete(TURN)
  await clock.advance(IDLE)
  await expectBand($, '✓ code-review  ✓ qa  ✓ qa-tour')
  await $.turn.complete({ ...TURN, turnId: 't2' })
  await clock.advance(IDLE)
  expect(fork.prompts).toHaveLength(2)
  await expectBand($, '✗ code-review  ✓ qa  ✓ qa-tour')
})

test('with nothing to fork the log is judged by haiku', async ($, on) => {
  const prompts: string[] = []
  const clock = engine(on, {
    store: { 'session:sess-1': ALL },
    messages: [{ role: 'user', text: 'now the login bug', toolUses: [] }],
    fork: () => unanswered('nothing-to-fork'),
    complete: (model, prompt) => {
      prompts.push(prompt)
      return answered('FEATURE: login bug\nSTALE: code-review, qa, qa-tour')
    },
  })
  await $.session.start(START)
  await $.tool.call(EDIT)
  await $.turn.complete(TURN)
  await clock.advance(IDLE)
  await settle(clock)
  expect(prompts).toEqual([expect.stringContaining('user: now the login bug')])
  await expectBand($, CROSSED)
})

test('only answered main-agent turns ask the fork', async ($, on) => {
  const fork = recorder([answered('FEATURE: x\nSTALE: none')])
  const clock = engine(on, { fork: fork.reply })
  await $.tool.call(EDIT)
  await $.turn.complete({ ...TURN, agentId: 'sub-1' })
  await $.turn.complete({ ...TURN, reason: 'aborted', isAborted: true })
  await clock.advance(IDLE)
  expect(fork.prompts).toEqual([])
  await $.turn.complete(TURN)
  await $.turn.complete({ ...TURN, turnId: 't2' })
  await clock.advance(IDLE)
  expect(fork.prompts).toHaveLength(1)
})

test('a check run asks the fork, an ordinary shell command does not', async ($, on) => {
  const fork = recorder([answered('FEATURE: x\nSTALE: none')])
  const clock = engine(on, { fork: fork.reply })
  await $.tool.call({ tool: 'Bash', command: 'ls -la' })
  await $.turn.complete(TURN)
  await clock.advance(IDLE)
  expect(fork.prompts).toEqual([])
  await $.tool.call({ tool: 'Bash', command: 'npm test' })
  await $.turn.complete({ ...TURN, turnId: 't2' })
  await clock.advance(IDLE)
  expect(fork.prompts).toHaveLength(1)
})

test('a written file asks the fork, a denied edit does not', async ($, on) => {
  const fork = recorder([answered('FEATURE: x\nSTALE: none')])
  let isDenied = true
  const clock = engine(on, {
    fork: fork.reply,
    toolCall: () => (isDenied ? { deny: 'not allowed' } : { result: {}, text: 'ok' }),
  })
  await $.tool.call(EDIT)
  await $.turn.complete(TURN)
  await clock.advance(IDLE)
  expect(fork.prompts).toEqual([])
  isDenied = false
  await $.tool.call({ tool: 'Write', file_path: '/w/b.ts', content: 'x' })
  await $.turn.complete({ ...TURN, turnId: 't2' })
  await clock.advance(IDLE)
  expect(fork.prompts).toHaveLength(1)
})

for (const [reason, asks] of [
  ['aborted', 2],
  ['empty-reply', 1],
] as const) {
  test(`a fork that ends ${reason} is asked ${asks === 2 ? 'again' : 'no more'} after the next turn`, async ($, on) => {
    const fork = recorder([unanswered(reason), answered('FEATURE: x\nSTALE: none')])
    const clock = engine(on, { fork: fork.reply })
    await $.tool.call(EDIT)
    await $.turn.complete(TURN)
    await clock.advance(IDLE)
    await $.turn.complete({ ...TURN, turnId: 't2' })
    await clock.advance(IDLE)
    expect(fork.prompts).toHaveLength(asks)
  })
}

test('clearing the session drops an unasked edit', async ($, on) => {
  const fork = recorder([answered('FEATURE: x\nSTALE: none')])
  const clock = engine(on, { fork: fork.reply })
  await $.tool.call(EDIT)
  await $.turn.complete({ ...TURN, reason: 'aborted', isAborted: true })
  await $.classic.SessionStart({ source: 'clear', session_id: 'sess-3' })
  await $.turn.complete(TURN)
  await clock.advance(IDLE)
  expect(fork.prompts).toEqual([])
})

test('a failed edit asks nothing', async ($, on) => {
  const fork = recorder([answered('FEATURE: x\nSTALE: qa')])
  const clock = engine(on, {
    store: { 'session:sess-1': ALL },
    fork: fork.reply,
    toolCall: () => ({ result: {}, text: 'no match', isError: true }),
  })
  await $.session.start(START)
  await $.tool.call(EDIT)
  await $.turn.complete(TURN)
  await clock.advance(IDLE)
  expect(fork.prompts).toEqual([])
  await expectBand($, '✓ code-review  ✓ qa  ✓ qa-tour')
})

test('a verdict that a checklist skill overtook is dropped', async ($, on) => {
  const held = gate()
  const clock = engine(on, {
    store: { 'session:sess-1': ALL },
    fork: async () => {
      await held.opened
      return answered('FEATURE: x\nSTALE: qa')
    },
  })
  await $.session.start(START)
  await $.tool.call(EDIT)
  await $.turn.complete(TURN)
  await clock.advance(IDLE)
  await $.skill.prompt({ skill: 'qa', text: 'qa' })
  held.open()
  await settle(clock)
  await expectBand($, '✓ code-review  ✓ qa  ✓ qa-tour')
})

test('a turn that ends while the fork runs is asked about when it returns', async ($, on) => {
  const gates = [gate(), gate()]
  const answers = ['FEATURE: x\nSTALE: qa', 'FEATURE: x\nSTALE: qa-tour']
  const prompts: string[] = []
  const clock = engine(on, {
    store: { 'session:sess-1': ALL },
    fork: async prompt => {
      const index = prompts.push(prompt) - 1
      await gates[index]?.opened
      return answered(answers[index] ?? '')
    },
  })
  await $.session.start(START)
  await $.tool.call(EDIT)
  await $.turn.complete(TURN)
  await clock.advance(IDLE)
  await $.tool.call(EDIT)
  await $.turn.complete({ ...TURN, turnId: 't2' })
  await clock.advance(IDLE)
  gates[0]?.open()
  await settle(clock)
  await expectBand($, '✓ code-review  ✓ qa  ✓ qa-tour')
  gates[1]?.open()
  await settle(clock)
  expect(prompts).toHaveLength(2)
  await expectBand($, '✓ code-review  ✓ qa  ✗ qa-tour')
})

test('stored checks show when the session starts and ask nothing', async ($, on) => {
  const models: string[] = []
  const clock = engine(on, {
    store: { 'session:sess-1': { ...NONE, 'qa-tour': true }, 'topic:sess-1': { name: 'csv export', at: 1 } },
    turns: 3,
    messages: [{ role: 'user', text: 'hi', toolUses: [] }],
    complete: model => {
      models.push(model)
      return answered('FEATURE: x\nSTALE: none')
    },
  })
  await $.session.start(START)
  await settle(clock)
  expect(models).toEqual([])
  await expectBand($, '✗ code-review  ✗ qa  ✓ qa-tour')
})

test('a session stored before the checklist starts crossed and asks nothing', async ($, on) => {
  const models: string[] = []
  const clock = engine(on, {
    store: { 'session:sess-1': { phase: 'manual QA', at: 1, source: 'skill' } },
    turns: 3,
    messages: [{ role: 'user', text: 'hi', toolUses: [] }],
    complete: model => {
      models.push(model)
      return answered('FEATURE: x\nSTALE: none')
    },
  })
  await $.session.start(START)
  await settle(clock)
  expect(models).toEqual([])
  await expectBand($, CROSSED)
})

test('a resumed session with nothing stored is named by haiku once', async ($, on) => {
  const held = gate()
  const models: string[] = []
  const clock = engine(on, {
    turns: 3,
    messages: [{ role: 'user', text: 'squash and commit', toolUses: [] }],
    complete: async model => {
      models.push(model)
      await held.opened
      return answered('FEATURE: csv export\nSTALE: none')
    },
  })
  await $.session.start(START)
  await settle(clock)
  await $.session.start(START)
  await settle(clock)
  held.open()
  await settle(clock)
  expect(models).toEqual(['haiku'])
  const result = await $.classic.UserPromptSubmit({ prompt: 'go', session_id: 'sess-1' })
  expect(result.sessionTitle).toBe('csv export')
})

test('resuming another session in place shows its checks', async ($, on) => {
  engine(on, { store: { 'session:sess-2': { ...NONE, 'code-review': true } } })
  await $.classic.SessionStart({ source: 'resume', session_id: 'sess-2' })
  await expectBand($, '✓ code-review  ✗ qa  ✗ qa-tour')
})

test('clearing the session crosses every check', async ($, on) => {
  engine(on, { store: { 'session:sess-1': ALL, 'topic:sess-1': { name: 'csv export', at: 1 } } })
  await $.session.start(START)
  await $.classic.SessionStart({ source: 'clear', session_id: 'sess-3' })
  await expectBand($, CROSSED)
})

test('a forked session inherits the checks and feature', async ($, on) => {
  engine(on, { store: { 'session:sess-1': { ...NONE, qa: true }, 'topic:sess-1': { name: 'csv export', at: 1 } } })
  await $.session.start(START)
  await $.classic.SessionStart({ source: 'fork', session_id: 'sess-2' })
  await $.classic.SessionStart({ source: 'clear', session_id: 'sess-3' })
  await $.classic.SessionStart({ source: 'resume', session_id: 'sess-2' })
  await expectBand($, '✗ code-review  ✓ qa  ✗ qa-tour')
  const result = await $.classic.UserPromptSubmit({ prompt: 'go', session_id: 'sess-2' })
  expect(result.sessionTitle).toBe('csv export')
})

test('a session forked from one with nothing recorded loads what the fork has stored', async ($, on) => {
  engine(on, { store: { 'session:sess-2': { ...NONE, qa: true } } })
  await $.session.start(START)
  await $.classic.SessionStart({ source: 'fork', session_id: 'sess-2' })
  await expectBand($, '✗ code-review  ✓ qa  ✗ qa-tour')
})

test('starting a session prunes the least recently used sessions', async ($, on) => {
  const others = Object.fromEntries(Array.from({ length: 300 }, (_, index) => [`session:s${index}`, ALL]))
  engine(on, { store: { 'session:sess-1': { ...NONE, qa: true }, ...others } })
  await $.session.start(START)
  await expectBand($, '✗ code-review  ✓ qa  ✗ qa-tour')
  await $.classic.SessionStart({ source: 'resume', session_id: 's299' })
  await expectBand($, '✓ code-review  ✓ qa  ✓ qa-tour')
  await $.classic.SessionStart({ source: 'resume', session_id: 's0' })
  await expectBand($, CROSSED)
})

test('the next prompt titles the session after its feature', async ($, on) => {
  engine(on, { store: { 'topic:sess-1': { name: 'dev-phase mod', at: 1 } } })
  const result = await $.classic.UserPromptSubmit({ prompt: 'go', session_id: 'sess-1' })
  expect(result.sessionTitle).toBe('dev-phase mod')
})

test('a renamed feature retitles the session the mod titled', async ($, on) => {
  const clock = engine(on, {
    store: { 'topic:sess-1': { name: 'dev-phase mod', at: 1 } },
    fork: () => answered('FEATURE: login bug\nSTALE: none'),
  })
  await $.session.start(START)
  await $.classic.UserPromptSubmit({ prompt: 'go', session_id: 'sess-1' })
  await $.tool.call(EDIT)
  await $.turn.complete(TURN)
  await clock.advance(IDLE)
  const result = await $.classic.UserPromptSubmit({
    prompt: 'go',
    session_id: 'sess-1',
    session_title: 'dev-phase mod',
  })
  expect(result.sessionTitle).toBe('login bug')
})

test('a title another hook set wins', async ($, on) => {
  engine(on, { store: { 'topic:sess-1': { name: 'dev-phase mod', at: 1 } }, promptTitle: 'chosen' })
  const result = await $.classic.UserPromptSubmit({ prompt: 'go', session_id: 'sess-1' })
  expect(result.sessionTitle).toBe('chosen')
})

test('a title the user chose stays', async ($, on) => {
  engine(on, { store: { 'topic:sess-1': { name: 'dev-phase mod', at: 1, titled: 'dev-phase mod' } } })
  const result = await $.classic.UserPromptSubmit({ prompt: 'go', session_id: 'sess-1', session_title: 'my band' })
  expect(result.sessionTitle).toBeUndefined()
})
