import { describe, expect, test } from 'claude-code/testing'

import { IDLE_MS } from '../core/phase'
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

const said = (text: string): Reply => ({ stopReason: 'stop', content: [{ type: 'text', text }] })
const failed: Reply = { stopReason: 'error', content: [], errorMessage: 'overloaded' }
const timedOut: Reply = { stopReason: 'aborted', content: [] }

const theme: BandTheme = {
  style: (text, { dim }) => (dim === true ? `~${text}` : text),
  fg: (color, text) => text,
}

const message = (value: Record<string, unknown>): PiEntry => ({ type: 'message', message: value })

const savedEntry = (data: unknown): PiEntry => ({ type: 'custom', customType: 'dev-phase', data })

const decided = savedEntry({ record: { phase: 'implementation', at: 1, source: 'log' }, topic: null })

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
  const reply = world.reply ?? (() => said('PHASE: none'))
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
  test('a fresh session shows no phase and asks nothing', async () => {
    const s = session()
    await s.start()
    expect(s.band()).toBe('● no phase yet')
    expect(s.widgets).toEqual(['dev-phase'])
    await s.advance(IDLE_MS)
    expect(s.prompts).toEqual([])
  })

  test('a delivered /skill: message sets its phase and its run asks no model', async () => {
    const s = session()
    await s.start()
    await s.run(async () => {
      await s.skill('commit')
      expect(s.band()).toBe('● wrap-up')
      await s.tool('edit', { path: '/u/w/a.ts' })
    })
    await s.advance(IDLE_MS)
    expect(s.prompts).toEqual([])
    expect(s.saved()).toEqual([{ record: { phase: 'wrap-up', at: 0, source: 'skill' }, topic: null }])
  })

  test('a /skill: typed but never delivered leaves the next run to the classifier', async () => {
    const s = session({ branch: [decided], reply: () => said('PHASE: agent QA') })
    await s.start('resume')
    await s.emit('input', { text: '/skill:commit' })
    await s.run(() => s.tool('edit', { path: '/u/w/a.ts' }))
    await s.advance(IDLE_MS)
    expect(s.prompts).toHaveLength(1)
    expect(s.band()).toBe('● agent QA')
  })

  test('the model reading a skill file sets its phase', async () => {
    const s = session()
    await s.start()
    await s.run(() => s.tool('read', { path: '~/.pi/agent/skills/code-review/SKILL.md' }))
    expect(s.band()).toBe('● code review')
  })

  test('the model printing a skill file in the shell sets its phase', async () => {
    const s = session()
    await s.start()
    await s.run(() => s.tool('bash', { command: `cat ${COMMIT_SKILL} | head -50` }))
    expect(s.band()).toBe('● wrap-up')
  })

  test('a failed read of a skill file keeps the phase', async () => {
    const s = session({ branch: [decided] })
    await s.start('resume')
    await s.tool('read', { path: REVIEW_SKILL }, true)
    await s.tool('bash', { command: `cat ${REVIEW_SKILL}` }, true)
    expect(s.band()).toBe('● implementation')
  })
})

describe('edits and classification', () => {
  test('an edit after review shows review fixes dimmed until the verdict names phase and feature', async () => {
    const s = session({ reply: () => said('PHASE: review fixes\nFEATURE: CSV export') })
    await s.start()
    await s.run(() => s.skill('code-review'))
    await s.run(() => s.tool('edit', { path: '/u/w/a.ts' }))
    expect(s.band()).toBe('~● ~review fixes')
    await s.advance(IDLE_MS - 1)
    expect(s.prompts).toEqual([])
    await s.advance(1)
    expect(s.prompts).toHaveLength(1)
    expect(s.prompts[0]).toContain('PHASE: <planning|')
    expect(s.prompts[0]).toContain('user: go on')
    expect(s.band()).toBe('● review fixes · CSV export')
    expect(s.name()).toBe('CSV export')
  })

  test('a phase change asks the terminal to redraw', async () => {
    const s = session()
    await s.start()
    const before = s.renders()
    await s.tool('edit', { path: '/u/w/a.ts' })
    expect(s.renders()).toBe(before + 1)
  })

  test('a failed edit keeps the phase', async () => {
    const s = session({ branch: [decided] })
    await s.start('resume')
    await s.run(() => s.tool('edit', { path: '/u/w/a.ts' }, true))
    await s.advance(IDLE_MS)
    expect(s.band()).toBe('● implementation')
    expect(s.prompts).toEqual([])
  })

  test('a conversation without tools is classified once', async () => {
    const s = session({ reply: () => said('PHASE: planning\nFEATURE: CSV export') })
    await s.start()
    await s.run()
    await s.advance(IDLE_MS)
    await s.run()
    await s.advance(IDLE_MS)
    expect(s.prompts).toHaveLength(1)
    expect(s.band()).toBe('● planning · CSV export')
  })

  test('commits and check runs, including the user\'s own, ask for a new verdict', async () => {
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
    const s = session({ reply: call => (call <= 2 ? failed : said('PHASE: implementation')) })
    await s.start()
    await s.run(() => s.tool('write', { path: '/u/w/a.ts' }))
    await s.advance(IDLE_MS)
    expect(s.prompts).toHaveLength(2)
    await s.run()
    await s.advance(IDLE_MS)
    expect(s.prompts).toHaveLength(3)
    expect(s.band()).toBe('● implementation')
  })

  test('a timed-out model falls back to the second model', async () => {
    const s = session({ reply: call => (call === 1 ? timedOut : said('PHASE: agent QA')) })
    await s.start()
    await s.run(() => s.tool('edit', { path: '/u/w/a.ts' }))
    await s.advance(IDLE_MS)
    expect(s.prompts).toHaveLength(2)
    expect(s.band()).toBe('● agent QA')
  })

  test('a reply cut off by the token limit is still used', async () => {
    const s = session({ reply: () => ({ stopReason: 'length', content: [{ type: 'text', text: 'PHASE: wrap-up\nFEA' }] }) })
    await s.start()
    await s.run(() => s.tool('edit', { path: '/u/w/a.ts' }))
    await s.advance(IDLE_MS)
    expect(s.band()).toBe('● wrap-up')
  })

  test('an unparseable reply is logged and leaves the phase', async () => {
    const s = session({ reply: () => said('I think it is implementation.') })
    await s.start()
    await s.run(() => s.tool('edit', { path: '/u/w/a.ts' }))
    await s.advance(IDLE_MS)
    expect(s.debugs).toEqual(['unparseable verdict: I think it is implementation.'])
    expect(s.band()).toBe('~● ~implementation')
  })

  test('a verdict without a feature keeps the feature, and the same feature keeps its timestamp', async () => {
    const topic = { name: 'CSV export', at: 1, titled: 'CSV export' }
    const s = session({
      branch: [message({ role: 'user', content: 'hi' }), savedEntry({ record: null, topic })],
      sessionName: 'CSV export',
      reply: call => said(call === 1 ? 'PHASE: implementation' : 'PHASE: agent QA\nFEATURE: CSV export'),
    })
    await s.start('resume')
    await s.run(() => s.tool('edit', { path: '/u/w/a.ts' }))
    await s.advance(IDLE_MS)
    expect(s.band()).toBe('● implementation · CSV export')
    await s.run(() => s.tool('edit', { path: '/u/w/b.ts' }))
    await s.advance(IDLE_MS)
    expect(s.saved().at(-1)).toEqual({ record: { phase: 'agent QA', at: 2 * IDLE_MS, source: 'log' }, topic })
  })

  test('an unchanged verdict saves no new entry', async () => {
    const s = session({ reply: () => said('PHASE: implementation') })
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
      isIdle: () => isIdle,
      reply: async () => {
        await held.opened
        return said('PHASE: agent QA')
      },
    })
    await s.start()
    await s.run(() => s.tool('edit', { path: '/u/w/a.ts' }))
    await s.advance(IDLE_MS)
    const count = s.saved().length
    isIdle = false
    held.open()
    await flush()
    expect(s.band()).toBe('● agent QA')
    expect(s.saved()).toHaveLength(count)
    await s.emit('turn_end')
    expect(s.saved().at(-1)).toEqual({ record: { phase: 'agent QA', at: IDLE_MS, source: 'log' }, topic: null })
  })

  test('a verdict overtaken by a skill is dropped', async () => {
    const held = gate()
    const s = session({
      reply: async () => {
        await held.opened
        return said('PHASE: implementation')
      },
    })
    await s.start()
    await s.run(() => s.tool('edit', { path: '/u/w/a.ts' }))
    await s.advance(IDLE_MS)
    await s.skill('commit')
    held.open()
    await flush()
    expect(s.prompts).toHaveLength(1)
    expect(s.band()).toBe('● wrap-up')
  })

  test('a run that settles while a verdict is pending is classified after it', async () => {
    const held = gate()
    const s = session({
      reply: async call => {
        if (call === 1) await held.opened
        return said(call === 1 ? 'PHASE: implementation' : 'PHASE: agent QA')
      },
    })
    await s.start()
    await s.run(() => s.tool('edit', { path: '/u/w/a.ts' }))
    await s.advance(IDLE_MS)
    await s.run(() => s.tool('bash', { command: 'npm test' }))
    await s.advance(IDLE_MS)
    expect(s.prompts).toHaveLength(1)
    held.open()
    await flush()
    expect(s.prompts).toHaveLength(2)
    expect(s.band()).toBe('● agent QA')
  })

  test('a queued question whose run was followed by another waits for that run', async () => {
    const held = gate()
    const s = session({
      reply: async call => {
        if (call === 1) await held.opened
        return said('PHASE: agent QA')
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
    expect(s.notices).toEqual(['dev-phase: no credentials for openrouter/google/gemini-2.5-flash-lite; phase labels are off'])
  })
})

describe('sessions and branches', () => {
  test('a none verdict clears the band and is remembered on the branch', async () => {
    const s = session({ branch: [decided] })
    await s.start('resume')
    await s.run(() => s.tool('edit', { path: '/u/w/a.ts' }))
    await s.advance(IDLE_MS)
    expect(s.band()).toBe('● no phase yet')
    expect(s.saved().at(-1)).toEqual({ record: null, topic: null })

    const resumed = session({ branch: [message({ role: 'user', content: 'hi' }), ...s.branch] })
    await resumed.start('resume')
    expect(resumed.prompts).toEqual([])
  })

  test('a saved phase is restored on start without asking', async () => {
    const record = { phase: 'manual QA', at: 5, source: 'log' }
    const s = session({
      branch: [
        message({ role: 'user', content: 'hi' }),
        savedEntry({ record, topic: { name: 'login bug', at: 5, titled: 'login bug' } }),
      ],
      sessionName: 'login bug',
    })
    await s.start('resume')
    expect(s.band()).toBe('● manual QA · login bug')
    expect(s.prompts).toEqual([])
  })

  test('a session with history but nothing saved is classified once on start', async () => {
    const s = session({
      branch: [message({ role: 'user', content: 'plan the export' })],
      reply: () => said('PHASE: planning'),
    })
    await s.start('resume')
    expect(s.prompts).toHaveLength(1)
    expect(s.band()).toBe('● planning')
  })

  test('a name the user chose is kept while the name the mod gave follows the feature', async () => {
    const topic = { name: 'login bug', at: 1, titled: 'old name' }
    const branch = [savedEntry({ record: null, topic })]
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
      branch: [message({ role: 'user', content: 'hi' }), savedEntry({ record: null, topic })],
      sessionName: 'login bug',
      reply: call => said(call === 1 ? 'PHASE: none\nFEATURE: none' : 'PHASE: implementation\nFEATURE: CSV export'),
    })
    await s.start('resume')
    await s.run(() => s.tool('edit', { path: '/u/w/a.ts' }))
    await s.advance(IDLE_MS)
    await s.run(() => s.tool('edit', { path: '/u/w/b.ts' }))
    await s.advance(IDLE_MS)
    expect(s.name()).toBe('CSV export')
  })

  test('moving to another branch shows its phase and drops a pending question', async () => {
    const s = session({ branch: [decided] })
    await s.start('resume')
    await s.run(() => s.tool('edit', { path: '/u/w/a.ts' }))
    await s.moveTo([
      message({ role: 'user', content: 'hi' }),
      savedEntry({ record: { phase: 'code review', at: 1, source: 'skill' }, topic: null }),
    ])
    expect(s.band()).toBe('● code review')
    await s.advance(IDLE_MS)
    expect(s.prompts).toEqual([])
  })

  test('moving to a branch with history but nothing saved classifies it', async () => {
    const s = session({ branch: [decided], reply: () => said('PHASE: planning') })
    await s.start('resume')
    await s.moveTo([message({ role: 'user', content: 'plan it' })])
    expect(s.prompts).toHaveLength(1)
    expect(s.band()).toBe('● planning')
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
      reply: async () => {
        await held.opened
        return said('PHASE: agent QA')
      },
    })
    await s.start()
    await s.run(() => s.tool('edit', { path: '/u/w/a.ts' }))
    await s.advance(IDLE_MS)
    await s.emit('session_shutdown', { reason: 'quit' })
    const count = s.saved().length
    held.open()
    await flush()
    expect(s.band()).toBe('~● ~implementation')
    expect(s.saved()).toHaveLength(count)
  })
})
