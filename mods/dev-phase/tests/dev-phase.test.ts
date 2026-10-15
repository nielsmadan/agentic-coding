import type { On, SessionMessage } from 'claude-code'
import { expect, mock, test } from 'claude-code/testing'
import type { Engine } from 'claude-code/testing'

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

const IDLE = 30_000

const EDIT = { tool: 'Edit', file_path: '/w/a.ts', old_string: 'a', new_string: 'b' } as const

const stored = (phase: string) => ({ phase, at: 1, source: 'skill' })

type World = {
  store?: Record<string, unknown>
  turns?: number
  messages?: SessionMessage[]
  fork?: (prompt: string) => unknown
  complete?: (model: string) => unknown
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
  on('model.fork', async ($, e) => ({ value: (await (world.fork ?? (() => answered('PHASE: none')))(e.prompt)) as never }))
  on('model.complete', async ($, e) => ({
    value: (await (world.complete ?? (() => answered('PHASE: none')))(e.model)) as never,
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

async function texts($: Engine): Promise<string[]> {
  const ui = await $.ui.mount({ ...BAND, surface: 'terminal' })
  const found = await ui.findAll({ type: 'Text' })
  await ui.unmount()
  return found.map(element => element.text)
}

async function expectShown($: Engine, text: string): Promise<void> {
  for (const surface of SURFACES) {
    const ui = await $.ui.mount({ ...BAND, surface })
    const found = await ui.findAll({ type: 'Text' })
    expect(found.map(element => element.text).join('')).toContain(text)
    await ui.unmount()
  }
}

async function settle(clock: { advance: (ms: number) => Promise<void> }): Promise<void> {
  await clock.advance(1)
  await clock.advance(1)
}

test('a fresh session shows that it has no phase yet', async ($, on) => {
  engine(on)
  await $.session.start(START)
  await expectShown($, 'no phase yet')
})

test('a workflow skill shows its phase', async ($, on) => {
  engine(on)
  await $.skill.prompt({ skill: 'code-review', text: 'review' })
  await expectShown($, 'code review')
})

test('an edit after code review shows review fixes until the model answers', async ($, on) => {
  const clock = engine(on, {
    store: { 'session:sess-1': stored('code review') },
    fork: () => answered('PHASE: code review'),
  })
  await $.session.start(START)
  await $.tool.call(EDIT)
  await expectShown($, 'review fixes')
  await $.turn.complete(TURN)
  await clock.advance(IDLE)
  await expectShown($, 'code review')
})

test('an idle session asks the fork and shows its phase and feature', async ($, on) => {
  const fork = recorder([answered('PHASE: agent QA\nFEATURE: dev-phase mod')])
  const clock = engine(on, { fork: fork.reply })
  await $.tool.call(EDIT)
  await $.turn.complete(TURN)
  await clock.advance(IDLE - 1)
  expect(fork.prompts).toEqual([])
  await clock.advance(1)
  expect(fork.prompts).toEqual([expect.stringContaining('PHASE: <planning|')])
  await expectShown($, 'agent QA')
  await expectShown($, 'dev-phase mod')
})

test('a reply before the idle wait moves the question to the next turn', async ($, on) => {
  const fork = recorder([answered('PHASE: agent QA')])
  const clock = engine(on, { fork: fork.reply })
  await $.tool.call(EDIT)
  await $.turn.complete(TURN)
  await $.turn.start({ text: 'next', turnId: 't2' })
  await clock.advance(IDLE)
  expect(fork.prompts).toEqual([])
  await $.turn.complete({ ...TURN, turnId: 't2' })
  await clock.advance(IDLE)
  expect(fork.prompts).toHaveLength(1)
  await expectShown($, 'agent QA')
})

test('an unanswered fork is asked again after the next turn', async ($, on) => {
  const fork = recorder([unanswered('api-error'), answered('PHASE: wrap-up')])
  const clock = engine(on, { store: { 'session:sess-1': stored('code review') }, fork: fork.reply })
  await $.session.start(START)
  await $.tool.call({ tool: 'Bash', command: 'git commit -m x' })
  await $.turn.complete(TURN)
  await clock.advance(IDLE)
  await expectShown($, 'code review')
  await $.turn.complete({ ...TURN, turnId: 't2' })
  await clock.advance(IDLE)
  expect(fork.prompts).toHaveLength(2)
  await expectShown($, 'wrap-up')
})

test('with nothing to fork the log is labelled by haiku', async ($, on) => {
  const clock = engine(on, {
    messages: [{ role: 'user', text: 'commit it', toolUses: [] }],
    fork: () => unanswered('nothing-to-fork'),
    complete: () => answered('PHASE: wrap-up'),
  })
  await $.tool.call(EDIT)
  await $.turn.complete(TURN)
  await clock.advance(IDLE)
  await settle(clock)
  await expectShown($, 'wrap-up')
})

test('only answered main-agent turns ask the fork', async ($, on) => {
  const fork = recorder([answered('PHASE: implementation')])
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

test('a failed edit leaves the phase as it was', async ($, on) => {
  engine(on, {
    store: { 'session:sess-1': stored('code review') },
    toolCall: () => ({ result: {}, text: 'no match', isError: true }),
  })
  await $.session.start(START)
  await $.tool.call(EDIT)
  await expectShown($, 'code review')
})

test('a verdict that a skill overtook is dropped', async ($, on) => {
  const held = gate()
  const clock = engine(on, {
    fork: async () => {
      await held.opened
      return answered('PHASE: implementation')
    },
  })
  await $.tool.call(EDIT)
  await $.turn.complete(TURN)
  await clock.advance(IDLE)
  await $.skill.prompt({ skill: 'code-review', text: 'review' })
  held.open()
  await settle(clock)
  await expectShown($, 'code review')
})

test('a turn that ends while the fork runs is asked about when it returns', async ($, on) => {
  const gates = [gate(), gate()]
  const answers = ['PHASE: agent QA', 'PHASE: QA fixes']
  const prompts: string[] = []
  const clock = engine(on, {
    fork: async prompt => {
      const index = prompts.push(prompt) - 1
      await gates[index]?.opened
      return answered(answers[index] ?? '')
    },
  })
  await $.tool.call(EDIT)
  await $.turn.complete(TURN)
  await clock.advance(IDLE)
  await $.tool.call(EDIT)
  await $.turn.complete({ ...TURN, turnId: 't2' })
  await clock.advance(IDLE)
  gates[0]?.open()
  await settle(clock)
  await expectShown($, 'implementation')
  gates[1]?.open()
  await settle(clock)
  expect(prompts).toHaveLength(2)
  await expectShown($, 'QA fixes')
})

test('a skill turn keeps the skill phase and asks no model', async ($, on) => {
  const fork = recorder([answered('PHASE: implementation')])
  const clock = engine(on, { fork: fork.reply })
  await $.skill.prompt({ skill: 'commit', text: 'commit' })
  await $.tool.call(EDIT)
  await $.turn.complete(TURN)
  await clock.advance(IDLE)
  expect(fork.prompts).toEqual([])
  await expectShown($, 'wrap-up')
})

test('a skill a subagent runs leaves the main phase alone', async ($, on) => {
  const held = gate()
  engine(on, {
    store: { 'session:sess-1': stored('implementation') },
    toolCall: () => held.opened.then(() => ({ result: {}, text: 'ok' })),
  })
  await $.session.start(START)
  const subagentSkill = { tool: 'Skill', skill: 'review-security', agentId: 'sub-1' } as const
  const call = $.tool.call(subagentSkill)
  await $.skill.prompt({ skill: 'review-security', text: 'review' })
  held.open()
  await call
  await expectShown($, 'implementation')
})

test('a model answer of none clears the band and is remembered', async ($, on) => {
  const models: string[] = []
  const clock = engine(on, {
    store: { 'session:sess-1': stored('code review'), 'topic:sess-1': { name: 'csv export', at: 1 } },
    turns: 3,
    messages: [{ role: 'user', text: 'what is the weather', toolUses: [] }],
    fork: () => answered('PHASE: none\nFEATURE: none'),
    complete: model => {
      models.push(model)
      return answered('PHASE: implementation')
    },
  })
  await $.session.start(START)
  await $.tool.call(EDIT)
  await $.turn.complete(TURN)
  await clock.advance(IDLE)
  expect(await texts($)).toEqual(['● no phase yet'])
  await $.classic.SessionStart({ source: 'resume', session_id: 'sess-1' })
  await settle(clock)
  expect(models).toEqual([])
  expect(await texts($)).toEqual(['● no phase yet'])
})

test('a stored phase and feature show when the session starts', async ($, on) => {
  engine(on, { store: { 'session:sess-1': stored('manual QA'), 'topic:sess-1': { name: 'csv export', at: 1 } } })
  await $.session.start(START)
  await expectShown($, 'manual QA')
  await expectShown($, 'csv export')
})

test('a resumed session with nothing stored is labelled by haiku once', async ($, on) => {
  const held = gate()
  const models: string[] = []
  const clock = engine(on, {
    turns: 3,
    messages: [{ role: 'user', text: 'squash and commit', toolUses: [] }],
    complete: async model => {
      models.push(model)
      await held.opened
      return answered('PHASE: wrap-up\nFEATURE: csv export')
    },
  })
  await $.session.start(START)
  await settle(clock)
  await $.session.start(START)
  await settle(clock)
  held.open()
  await settle(clock)
  expect(models).toEqual(['haiku'])
  await expectShown($, 'wrap-up')
  await expectShown($, 'csv export')
})

test('a session with a stored phase asks haiku nothing on start', async ($, on) => {
  const models: string[] = []
  const clock = engine(on, {
    store: { 'session:sess-1': stored('planning') },
    turns: 3,
    messages: [{ role: 'user', text: 'plan it', toolUses: [] }],
    complete: model => {
      models.push(model)
      return answered('PHASE: wrap-up')
    },
  })
  await $.session.start(START)
  await settle(clock)
  expect(models).toEqual([])
  await expectShown($, 'planning')
})

test('resuming another session in place shows its phase', async ($, on) => {
  engine(on, { store: { 'session:sess-2': stored('QA fixes') } })
  await $.classic.SessionStart({ source: 'resume', session_id: 'sess-2' })
  await expectShown($, 'QA fixes')
})

test('clearing the session empties the band', async ($, on) => {
  engine(on, { store: { 'session:sess-1': stored('code review'), 'topic:sess-1': { name: 'csv export', at: 1 } } })
  await $.session.start(START)
  await $.classic.SessionStart({ source: 'clear', session_id: 'sess-3' })
  expect(await texts($)).toEqual(['● no phase yet'])
})

test('a forked session inherits the phase and feature', async ($, on) => {
  engine(on, { store: { 'session:sess-1': stored('code review'), 'topic:sess-1': { name: 'csv export', at: 1 } } })
  await $.session.start(START)
  await $.classic.SessionStart({ source: 'fork', session_id: 'sess-2' })
  await $.classic.SessionStart({ source: 'clear', session_id: 'sess-3' })
  await $.classic.SessionStart({ source: 'resume', session_id: 'sess-2' })
  await expectShown($, 'code review')
  await expectShown($, 'csv export')
})

test('starting a session prunes the least recently used sessions', async ($, on) => {
  const others = Object.fromEntries(
    Array.from({ length: 300 }, (_, index) => [`session:s${index}`, stored('implementation')]),
  )
  engine(on, { store: { 'session:sess-1': stored('wrap-up'), ...others } })
  await $.session.start(START)
  await expectShown($, 'wrap-up')
  await $.classic.SessionStart({ source: 'resume', session_id: 's299' })
  await expectShown($, 'implementation')
  await $.classic.SessionStart({ source: 'resume', session_id: 's0' })
  expect(await texts($)).toEqual(['● no phase yet'])
})

test('the next prompt titles the session after its feature', async ($, on) => {
  engine(on, { store: { 'topic:sess-1': { name: 'dev-phase mod', at: 1 } } })
  const result = await $.classic.UserPromptSubmit({ prompt: 'go', session_id: 'sess-1' })
  expect(result.sessionTitle).toBe('dev-phase mod')
})

test('a renamed feature retitles the session the mod titled', async ($, on) => {
  const clock = engine(on, {
    store: { 'topic:sess-1': { name: 'dev-phase mod', at: 1 } },
    fork: () => answered('PHASE: implementation\nFEATURE: login bug'),
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
