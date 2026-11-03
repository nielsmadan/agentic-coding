import { describe, expect, test } from 'claude-code/testing'

import { IDLE_MS, UNCHECKED } from '../core/checklist'
import { createDevPhase } from '../pi/extension'
import type { Deps, Pi, PiContext } from '../pi/extension'
import type { BandTheme } from '../pi/band'
import type { PiEntry } from '../pi/transcript'

type FakeSignal = { aborted: boolean }
type Reply = { stopReason: string; content: { type: string; text?: string }[]; errorMessage?: string }
type Timer = { at: number; run: () => void; isCleared: boolean }
type World = {
  branch?: PiEntry[]
  mode?: string
  sessionName?: string
  hasAuth?: boolean
  isIdle?: () => boolean
  reply?: (call: number) => Reply | Promise<Reply>
}

const COMMIT_SKILL = '/u/.pi/agent/skills/commit/SKILL.md'
const REVIEW_SKILL = '/u/.pi/agent/skills/code-review/SKILL.md'
const QA_SKILL = '/u/.pi/agent/skills/qa/SKILL.md'
const PLAN_SKILL = '/u/.pi/agent/skills/plan/SKILL.md'

const said = (text: string): Reply => ({ stopReason: 'stop', content: [{ type: 'text', text }] })
const failed: Reply = { stopReason: 'error', content: [], errorMessage: 'overloaded' }
const timedOut: Reply = { stopReason: 'aborted', content: [] }

const theme: BandTheme = { fg: (color, text) => text }

const ALL = { 'code-review': true, qa: true, 'qa-tour': true }

const CROSSED = '✗ code-review  ✗ qa  ✗ qa-tour'

const TICKED = '✓ code-review  ✓ qa  ✓ qa-tour'

const message = (value: Record<string, unknown>): PiEntry => ({ type: 'message', message: value })

const savedEntry = (data: unknown): PiEntry => ({ type: 'custom', customType: 'dev-phase', data })

const decided = savedEntry({ checks: ALL, topic: null })

function gate() {
  let open: () => void = () => undefined
  const opened = new Promise<void>(resolve => {
    open = resolve
  })
  return { open, opened }
}

async function flush(): Promise<void> {
  for (let i = 0; i < 20; i += 1) await Promise.resolve()
}

function session(world: World = {}) {
  const handlers = new Map<string, (event: never, ctx: PiContext<FakeSignal>) => unknown>()
  let branch = [...(world.branch ?? [])]
  const prompts: string[] = []
  const notices: string[] = []
  const debugs: string[] = []
  const timers: Timer[] = []
  const widgets: string[] = []
  let renders = 0
  let now = 0
  let name = world.sessionName
  let band: (() => string) | undefined

  const deps: Deps<FakeSignal> = {
    setTimer: (run, ms) => timers.push({ at: now + ms, run, isCleared: false }) - 1,
    clearTimer: handle => {
      const timer = timers[handle as number]
      if (timer !== undefined) timer.isCleared = true
    },
    now: () => now,
    abortController: () => {
      const signal = { aborted: false }
      return { signal, abort: () => (signal.aborted = true) }
    },
    deadline: signal => signal,
    truncate: text => text,
    home: '/u',
    debug: text => debugs.push(text),
  }
  const reply = world.reply ?? (() => said('FEATURE: none\nSTALE: none'))
  const ctx: PiContext<FakeSignal> = {
    mode: world.mode ?? 'tui',
    cwd: '/u/w',
    ui: {
      setWidget: (key, content) => {
        widgets.push(key)
        const widget = content({ requestRender: () => (renders += 1) }, theme)
        band = () => widget.render(200)[0] ?? ''
      },
      notify: text => notices.push(text),
    },
    sessionManager: { getBranch: () => branch },
    modelRegistry: {
      find: (provider, id) => ({ provider, id }),
      hasConfiguredAuth: () => world.hasAuth ?? true,
      streamSimple: (model, context) => {
        prompts.push(context.messages[0]?.content ?? '')
        const call = prompts.length
        return { result: async () => reply(call) }
      },
    },
    isIdle: world.isIdle ?? (() => true),
  }
  const pi: Pi<FakeSignal> = {
    on: (event, handler) => handlers.set(event, handler),
    appendEntry: (customType, data) => branch.push({ type: 'custom', customType, data }),
    setSessionName: next => {
      name = next
    },
    getSessionName: () => name,
    getCommands: () => [
      { name: 'skill:commit', source: 'skill', sourceInfo: { path: COMMIT_SKILL } },
      { name: 'skill:code-review', source: 'skill', sourceInfo: { path: REVIEW_SKILL } },
      { name: 'skill:qa', source: 'skill', sourceInfo: { path: QA_SKILL } },
      { name: 'skill:plan', source: 'skill', sourceInfo: { path: PLAN_SKILL } },
    ],
  }
  createDevPhase(deps)(pi)

  const emit = async (event: string, payload: object = {}): Promise<void> => {
    await handlers.get(event)?.(payload as never, ctx)
    await flush()
  }

  const tool = (toolName: string, input: Record<string, unknown>, isError = false) =>
    emit('tool_result', { toolName, input, isError })

  const skill = (skillName: string) =>
    emit('message_end', {
      message: { role: 'user', content: `<skill name="${skillName}" location="/s">\n\nbody\n</skill>` },
    })

  const run = async (work: () => Promise<void> = async () => undefined, end = { stop: 'stop', aborted: false }) => {
    await emit('agent_start')
    branch.push(message({ role: 'user', content: 'go on' }))
    await work()
    branch.push(message({ role: 'assistant', content: [{ type: 'text', text: 'Done.' }], stopReason: end.stop }))
    await emit('turn_end')
    await emit('agent_end', { messages: [{ role: 'assistant', stopReason: end.stop }] })
    await emit('agent_settled', { aborted: end.aborted })
  }

  const advance = async (ms: number): Promise<void> => {
    now += ms
    const due = timers.filter(timer => !timer.isCleared && timer.at <= now)
    due.forEach(timer => (timer.isCleared = true))
    due.forEach(timer => timer.run())
    await flush()
  }

  const saved = () => branch.filter(entry => entry.type === 'custom').map(entry => entry.data)

  const moveTo = async (entries: PiEntry[]) => {
    branch = entries
    await emit('session_tree')
  }

  return {
    get branch() {
      return branch
    },
    prompts,
    notices,
    debugs,
    widgets,
    emit,
    tool,
    skill,
    run,
    advance,
    saved,
    moveTo,
    renders: () => renders,
    band: () => band?.() ?? '',
    name: () => name,
    start: (reason = 'startup') => emit('session_start', { reason }),
  }
}

describe('skills', () => {
  test('a fresh session shows every check crossed and asks nothing', async () => {
    const s = session()
    await s.start()
    expect(s.band()).toBe(CROSSED)
    expect(s.widgets).toEqual(['dev-phase'])
    await s.advance(IDLE_MS)
    expect(s.prompts).toEqual([])
  })

  test('a delivered /skill: message ticks its check and its run asks the model', async () => {
    const s = session()
    await s.start()
    await s.run(async () => {
      await s.skill('qa')
      expect(s.band()).toBe('✗ code-review  ✓ qa  ✗ qa-tour')
    })
    await s.advance(IDLE_MS)
    expect(s.prompts).toEqual([expect.stringContaining('Set now: qa.')])
    expect(s.saved()).toEqual([{ checks: { ...UNCHECKED, qa: true }, topic: null }])
  })

  test('a /skill: typed but never delivered ticks nothing', async () => {
    const s = session()
    await s.start()
    await s.emit('input', { text: '/skill:qa' })
    await s.run(() => s.tool('edit', { path: '/u/w/a.ts' }))
    await s.advance(IDLE_MS)
    expect(s.prompts).toHaveLength(1)
    expect(s.band()).toBe(CROSSED)
  })

  test('the model reading a skill file ticks its check', async () => {
    const s = session()
    await s.start()
    await s.run(() => s.tool('read', { path: '~/.pi/agent/skills/code-review/SKILL.md' }))
    expect(s.band()).toBe('✓ code-review  ✗ qa  ✗ qa-tour')
  })

  test('the model printing a skill file in the shell ticks its check', async () => {
    const s = session()
    await s.start()
    await s.run(() => s.tool('bash', { command: `cat ${QA_SKILL} | head -50` }))
    expect(s.band()).toBe('✗ code-review  ✓ qa  ✗ qa-tour')
  })

  test('a failed read of a skill file ticks nothing', async () => {
    const s = session()
    await s.start()
    await s.tool('read', { path: REVIEW_SKILL }, true)
    await s.tool('bash', { command: `cat ${REVIEW_SKILL}` }, true)
    expect(s.band()).toBe(CROSSED)
  })

  test('another skill without edits ticks nothing and asks nothing', async () => {
    const s = session({ branch: [decided] })
    await s.start('resume')
    await s.run(() => s.skill('commit'))
    await s.advance(IDLE_MS)
    expect(s.prompts).toEqual([])
    expect(s.band()).toBe(TICKED)
  })

  test('a planning skill asks the model after its run, which can start a new feature', async () => {
    const s = session({ branch: [decided], reply: () => said('FEATURE: login bug\nSTALE: code-review, qa, qa-tour') })
    await s.start('resume')
    await s.run(() => s.tool('read', { path: PLAN_SKILL }))
    await s.advance(IDLE_MS)
    expect(s.prompts).toHaveLength(1)
    expect(s.band()).toBe(CROSSED)
    expect(s.name()).toBe('login bug')
  })
})

describe('edits and classification', () => {
  test('an edit asks the model after the idle wait, which crosses what went stale and names the feature', async () => {
    const s = session({ branch: [decided], reply: () => said('FEATURE: CSV export\nSTALE: qa') })
    await s.start('resume')
    await s.run(() => s.tool('edit', { path: '/u/w/a.ts' }))
    await s.advance(IDLE_MS - 1)
    expect(s.prompts).toEqual([])
    await s.advance(1)
    expect(s.prompts).toHaveLength(1)
    expect(s.prompts[0]).toContain('Set now: code-review, qa, qa-tour.')
    expect(s.prompts[0]).toContain('user: go on')
    expect(s.band()).toBe('✓ code-review  ✗ qa  ✓ qa-tour')
    expect(s.name()).toBe('CSV export')
  })

  test('a check change asks the terminal to redraw', async () => {
    const s = session()
    await s.start()
    const before = s.renders()
    await s.skill('qa')
    expect(s.renders()).toBe(before + 1)
  })

  test('an ordinary shell command or an edit without a path asks nothing', async () => {
    const s = session({ branch: [decided] })
    await s.start('resume')
    await s.run(async () => {
      await s.tool('bash', { command: 'ls -la' })
      await s.tool('edit', {})
    })
    await s.advance(IDLE_MS)
    expect(s.prompts).toEqual([])
  })

  test('a failed edit asks nothing', async () => {
    const s = session({ branch: [decided] })
    await s.start('resume')
    await s.run(() => s.tool('edit', { path: '/u/w/a.ts' }, true))
    await s.advance(IDLE_MS)
    expect(s.band()).toBe(TICKED)
    expect(s.prompts).toEqual([])
  })

  test('a conversation without tools is classified once', async () => {
    const s = session({ reply: () => said('FEATURE: CSV export\nSTALE: none') })
    await s.start()
    await s.run()
    await s.advance(IDLE_MS)
    await s.run()
    await s.advance(IDLE_MS)
    expect(s.prompts).toHaveLength(1)
    expect(s.name()).toBe('CSV export')
  })

  test("commits and check runs, including the user's own, ask for a new verdict", async () => {
    const s = session({ branch: [decided] })
    await s.start('resume')
    await s.run(() => s.tool('bash', { command: 'git commit -m "x"' }))
    await s.advance(IDLE_MS)
    await s.emit('user_bash', { command: 'npm test' })
    await s.run()
    await s.advance(IDLE_MS)
    expect(s.prompts).toHaveLength(2)
  })

  test('a run that starts within the idle wait moves the question to its own end', async () => {
    const s = session({ branch: [decided] })
    await s.start('resume')
    await s.run(() => s.tool('edit', { path: '/u/w/a.ts' }))
    await s.advance(IDLE_MS / 2)
    await s.run()
    await s.advance(IDLE_MS / 2)
    expect(s.prompts).toEqual([])
    await s.advance(IDLE_MS / 2)
    expect(s.prompts).toHaveLength(1)
  })

  test('an aborted run asks nothing', async () => {
    const s = session({ branch: [decided] })
    await s.start('resume')
    await s.run(() => s.tool('edit', { path: '/u/w/a.ts' }), { stop: 'stop', aborted: true })
    await s.advance(IDLE_MS)
    expect(s.prompts).toEqual([])
  })

  test('a run that ended in an error asks nothing', async () => {
    const s = session({ branch: [decided] })
    await s.start('resume')
    await s.run(() => s.tool('edit', { path: '/u/w/a.ts' }), { stop: 'error', aborted: false })
    await s.advance(IDLE_MS)
    expect(s.prompts).toEqual([])
  })
})

describe('model replies', () => {
  test('a failed classification is asked again after the next run', async () => {
    const s = session({ reply: call => (call <= 2 ? failed : said('FEATURE: CSV export\nSTALE: none')) })
    await s.start()
    await s.run(() => s.tool('write', { path: '/u/w/a.ts' }))
    await s.advance(IDLE_MS)
    expect(s.prompts).toHaveLength(2)
    await s.run()
    await s.advance(IDLE_MS)
    expect(s.prompts).toHaveLength(3)
    expect(s.name()).toBe('CSV export')
  })

  test('a timed-out model falls back to the second model', async () => {
    const s = session({ branch: [decided], reply: call => (call === 1 ? timedOut : said('FEATURE: x\nSTALE: qa')) })
    await s.start('resume')
    await s.run(() => s.tool('edit', { path: '/u/w/a.ts' }))
    await s.advance(IDLE_MS)
    expect(s.prompts).toHaveLength(2)
    expect(s.band()).toBe('✓ code-review  ✗ qa  ✓ qa-tour')
  })

  test('a reply cut off by the token limit is still used', async () => {
    const s = session({ reply: () => ({ stopReason: 'length', content: [{ type: 'text', text: 'FEATURE: CSV export\nSTA' }] }) })
    await s.start()
    await s.run(() => s.tool('edit', { path: '/u/w/a.ts' }))
    await s.advance(IDLE_MS)
    expect(s.name()).toBe('CSV export')
  })

  test('an unparseable reply is logged and leaves the checks', async () => {
    const s = session({ branch: [decided], reply: () => said('I think qa is stale.') })
    await s.start('resume')
    await s.run(() => s.tool('edit', { path: '/u/w/a.ts' }))
    await s.advance(IDLE_MS)
    expect(s.debugs).toEqual(['unparseable verdict: I think qa is stale.'])
    expect(s.band()).toBe(TICKED)
  })

  test('a verdict without a feature keeps the feature, and the same feature keeps its timestamp', async () => {
    const topic = { name: 'CSV export', at: 1, titled: 'CSV export' }
    const s = session({
      branch: [message({ role: 'user', content: 'hi' }), savedEntry({ checks: ALL, topic })],
      sessionName: 'CSV export',
      reply: call => said(call === 1 ? 'STALE: qa' : 'FEATURE: CSV export\nSTALE: qa-tour'),
    })
    await s.start('resume')
    await s.run(() => s.tool('edit', { path: '/u/w/a.ts' }))
    await s.advance(IDLE_MS)
    expect(s.band()).toBe('✓ code-review  ✗ qa  ✓ qa-tour')
    await s.run(() => s.tool('edit', { path: '/u/w/b.ts' }))
    await s.advance(IDLE_MS)
    expect(s.saved().at(-1)).toEqual({ checks: { ...UNCHECKED, 'code-review': true }, topic })
  })

  test('an unchanged verdict saves no new entry', async () => {
    const s = session({ reply: () => said('FEATURE: CSV export\nSTALE: none') })
    await s.start()
    await s.run(() => s.tool('edit', { path: '/u/w/a.ts' }))
    await s.advance(IDLE_MS)
    const count = s.saved().length
    await s.run(() => s.tool('edit', { path: '/u/w/b.ts' }))
    await s.advance(IDLE_MS)
    expect(s.prompts).toHaveLength(2)
    expect(s.saved()).toHaveLength(count)
  })

  test('a verdict that arrives mid-run is saved at the next turn boundary', async () => {
    let isIdle = true
    const held = gate()
    const s = session({
      branch: [decided],
      isIdle: () => isIdle,
      reply: async () => {
        await held.opened
        return said('STALE: qa')
      },
    })
    await s.start('resume')
    await s.run(() => s.tool('edit', { path: '/u/w/a.ts' }))
    await s.advance(IDLE_MS)
    const count = s.saved().length
    isIdle = false
    held.open()
    await flush()
    expect(s.band()).toBe('✓ code-review  ✗ qa  ✓ qa-tour')
    expect(s.saved()).toHaveLength(count)
    await s.emit('turn_end')
    expect(s.saved().at(-1)).toEqual({ checks: { ...ALL, qa: false }, topic: null })
  })

  test('a verdict overtaken by a checklist skill is dropped', async () => {
    const held = gate()
    const s = session({
      branch: [decided],
      reply: async () => {
        await held.opened
        return said('STALE: qa')
      },
    })
    await s.start('resume')
    await s.run(() => s.tool('edit', { path: '/u/w/a.ts' }))
    await s.advance(IDLE_MS)
    await s.skill('qa')
    held.open()
    await flush()
    expect(s.prompts).toHaveLength(1)
    expect(s.band()).toBe(TICKED)
  })

  test('a run that settles while a verdict is pending is classified after it', async () => {
    const held = gate()
    const s = session({
      branch: [decided],
      reply: async call => {
        if (call === 1) await held.opened
        return said(call === 1 ? 'STALE: none' : 'STALE: qa')
      },
    })
    await s.start('resume')
    await s.run(() => s.tool('edit', { path: '/u/w/a.ts' }))
    await s.advance(IDLE_MS)
    await s.run(() => s.tool('bash', { command: 'npm test' }))
    await s.advance(IDLE_MS)
    expect(s.prompts).toHaveLength(1)
    held.open()
    await flush()
    expect(s.prompts).toHaveLength(2)
    expect(s.band()).toBe('✓ code-review  ✗ qa  ✓ qa-tour')
  })

  test('a queued question whose run was followed by another waits for that run', async () => {
    const held = gate()
    const s = session({
      reply: async call => {
        if (call === 1) await held.opened
        return said('STALE: none')
      },
    })
    await s.start()
    await s.run(() => s.tool('edit', { path: '/u/w/a.ts' }))
    await s.advance(IDLE_MS)
    await s.run(() => s.tool('bash', { command: 'npm test' }))
    await s.advance(IDLE_MS)
    await s.emit('agent_start')
    held.open()
    await flush()
    expect(s.prompts).toHaveLength(1)
    await s.emit('agent_end', { messages: [{ role: 'assistant', stopReason: 'stop' }] })
    await s.emit('agent_settled', { aborted: false })
    await s.advance(IDLE_MS)
    expect(s.prompts).toHaveLength(2)
  })

  test('missing credentials are reported once', async () => {
    const s = session({ hasAuth: false })
    await s.start()
    await s.run(() => s.tool('edit', { path: '/u/w/a.ts' }))
    await s.advance(IDLE_MS)
    await s.run(() => s.tool('edit', { path: '/u/w/b.ts' }))
    await s.advance(IDLE_MS)
    expect(s.notices).toEqual([
      'dev-phase: no credentials for openrouter/google/gemini-2.5-flash-lite; feature names and check resets are off',
    ])
  })
})

describe('interrupted and held checks', () => {
  test('an aborted run takes back the checks its skills newly set', async () => {
    const s = session({ branch: [message({ role: 'user', content: 'hi' }), savedEntry({ checks: { ...UNCHECKED, qa: true }, topic: null })] })
    await s.start('resume')
    await s.run(
      async () => {
        await s.skill('qa')
        await s.skill('code-review')
        expect(s.band()).toBe('✓ code-review  ✓ qa  ✗ qa-tour')
      },
      { stop: 'aborted', aborted: true },
    )
    expect(s.band()).toBe('✗ code-review  ✓ qa  ✗ qa-tour')
    expect(s.saved().at(-1)).toEqual({ checks: { ...UNCHECKED, qa: true }, topic: null })
  })

  test('a verdict cannot cross a check its own run ticked, but crosses older ones', async () => {
    const s = session({
      branch: [message({ role: 'user', content: 'hi' }), savedEntry({ checks: { ...UNCHECKED, qa: true }, topic: null })],
      reply: () => said('FEATURE: x\nSTALE: code-review, qa'),
    })
    await s.start('resume')
    await s.run(async () => {
      await s.skill('code-review')
      await s.tool('edit', { path: '/u/w/a.ts' })
    })
    await s.advance(IDLE_MS)
    expect(s.prompts).toHaveLength(1)
    expect(s.band()).toBe('✓ code-review  ✗ qa  ✗ qa-tour')
  })
})

describe('sessions and branches', () => {
  test('a verdict is remembered on the branch so a resume asks nothing', async () => {
    const s = session()
    await s.start()
    await s.run(() => s.tool('edit', { path: '/u/w/a.ts' }))
    await s.advance(IDLE_MS)
    expect(s.saved().at(-1)).toEqual({ checks: UNCHECKED, topic: null })

    const resumed = session({ branch: [message({ role: 'user', content: 'hi' }), ...s.branch] })
    await resumed.start('resume')
    expect(resumed.prompts).toEqual([])
  })

  test('saved checks are restored on start without asking', async () => {
    const s = session({
      branch: [
        message({ role: 'user', content: 'hi' }),
        savedEntry({ checks: { ...UNCHECKED, qa: true }, topic: { name: 'login bug', at: 5, titled: 'login bug' } }),
      ],
      sessionName: 'login bug',
    })
    await s.start('resume')
    expect(s.band()).toBe('✗ code-review  ✓ qa  ✗ qa-tour')
    expect(s.prompts).toEqual([])
  })

  test('a session saved before the checklist starts crossed, keeps its name and asks nothing', async () => {
    const topic = { name: 'login bug', at: 5, titled: 'old name' }
    const s = session({
      branch: [
        message({ role: 'user', content: 'hi' }),
        savedEntry({ record: { phase: 'manual QA', at: 5, source: 'log' }, topic }),
      ],
      sessionName: 'old name',
    })
    await s.start('resume')
    expect(s.band()).toBe(CROSSED)
    expect(s.name()).toBe('login bug')
    expect(s.prompts).toEqual([])
  })

  test('a session with history but nothing saved is classified once on start', async () => {
    const s = session({
      branch: [message({ role: 'user', content: 'plan the export' })],
      reply: () => said('FEATURE: CSV export\nSTALE: none'),
    })
    await s.start('resume')
    expect(s.prompts).toHaveLength(1)
    expect(s.name()).toBe('CSV export')
  })

  test('a name the user chose is kept while the name the mod gave follows the feature', async () => {
    const topic = { name: 'login bug', at: 1, titled: 'old name' }
    const branch = [savedEntry({ checks: UNCHECKED, topic })]
    const chosen = session({ branch, sessionName: 'mine' })
    await chosen.start('resume')
    expect(chosen.name()).toBe('mine')

    const given = session({ branch, sessionName: 'old name' })
    await given.start('resume')
    expect(given.name()).toBe('login bug')
  })

  test('the mod keeps naming the session after a verdict cleared the feature', async () => {
    const topic = { name: 'login bug', at: 1, titled: 'login bug' }
    const s = session({
      branch: [message({ role: 'user', content: 'hi' }), savedEntry({ checks: UNCHECKED, topic })],
      sessionName: 'login bug',
      reply: call => said(call === 1 ? 'FEATURE: none\nSTALE: none' : 'FEATURE: CSV export\nSTALE: none'),
    })
    await s.start('resume')
    await s.run(() => s.tool('edit', { path: '/u/w/a.ts' }))
    await s.advance(IDLE_MS)
    await s.run(() => s.tool('edit', { path: '/u/w/b.ts' }))
    await s.advance(IDLE_MS)
    expect(s.name()).toBe('CSV export')
  })

  test('moving to another branch shows its checks and drops a pending question', async () => {
    const s = session({ branch: [decided] })
    await s.start('resume')
    await s.run(() => s.tool('edit', { path: '/u/w/a.ts' }))
    await s.moveTo([
      message({ role: 'user', content: 'hi' }),
      savedEntry({ checks: { ...UNCHECKED, 'code-review': true }, topic: null }),
    ])
    expect(s.band()).toBe('✓ code-review  ✗ qa  ✗ qa-tour')
    await s.advance(IDLE_MS)
    expect(s.prompts).toEqual([])
  })

  test('moving to another branch drops a verdict that was still on its way', async () => {
    const held = gate()
    const s = session({
      branch: [decided],
      reply: async () => {
        await held.opened
        return said('STALE: qa')
      },
    })
    await s.start('resume')
    await s.run(() => s.tool('edit', { path: '/u/w/a.ts' }))
    await s.advance(IDLE_MS)
    expect(s.prompts).toHaveLength(1)
    await s.moveTo([message({ role: 'user', content: 'hi' }), savedEntry({ checks: ALL, topic: null })])
    held.open()
    await flush()
    expect(s.band()).toBe(TICKED)
  })

  test('moving to a branch with history but nothing saved classifies it', async () => {
    const s = session({ branch: [decided], reply: () => said('FEATURE: CSV export\nSTALE: none') })
    await s.start('resume')
    await s.moveTo([message({ role: 'user', content: 'plan it' })])
    expect(s.prompts).toHaveLength(1)
    expect(s.band()).toBe(CROSSED)
    expect(s.name()).toBe('CSV export')
  })

  test('outside the terminal UI nothing is drawn or asked', async () => {
    const s = session({ mode: 'print', branch: [message({ role: 'user', content: 'hi' })] })
    await s.start()
    await s.run(() => s.tool('edit', { path: '/u/w/a.ts' }))
    await s.advance(IDLE_MS)
    expect(s.widgets).toEqual([])
    expect(s.prompts).toEqual([])
    expect(s.saved()).toEqual([])
  })

  test('shutdown cancels a pending question', async () => {
    const s = session()
    await s.start()
    await s.run(() => s.tool('edit', { path: '/u/w/a.ts' }))
    await s.emit('session_shutdown', { reason: 'quit' })
    await s.advance(IDLE_MS)
    expect(s.prompts).toEqual([])
  })

  test('a verdict that arrives after shutdown is discarded', async () => {
    const held = gate()
    const s = session({
      branch: [decided],
      reply: async () => {
        await held.opened
        return said('STALE: qa')
      },
    })
    await s.start('resume')
    await s.run(() => s.tool('edit', { path: '/u/w/a.ts' }))
    await s.advance(IDLE_MS)
    await s.emit('session_shutdown', { reason: 'quit' })
    const count = s.saved().length
    held.open()
    await flush()
    expect(s.band()).toBe(TICKED)
    expect(s.saved()).toHaveLength(count)
  })
})
