import type { DevPhase, DevPhaseRecord, DevPhaseSource } from '../types'
import {
  digest,
  digestPrompt,
  IDLE_MS,
  isCheckpoint,
  MAX_TOKENS,
  MODEL_TIMEOUT_MS,
  phaseOfSkill,
  provisionalPhase,
  retitle,
  verdictState,
} from '../core/phase'
import type { DevPhaseState } from '../core/phase'
import { bandLine } from './band'
import type { BandTheme } from './band'
import {
  ENTRY_TYPE,
  hasHistory,
  lastAssistantStop,
  latestState,
  latestTitle,
  skillFromCommand,
  skillFromUserMessage,
  skillResolver,
  toDigestMessages,
} from './transcript'
import type { PiCommand, PiEntry, SkillOf } from './transcript'

export type Signal = { readonly aborted: boolean }

export type Deps<S extends Signal = Signal> = {
  setTimer(run: () => void, ms: number): unknown
  clearTimer(handle: unknown): void
  now(): number
  abortController(): { signal: S; abort(): void }
  deadline(signal: S, ms: number): S
  truncate(text: string, width: number): string
  home: string
  debug(text: string): void
}

type ModelReply = { stopReason: string; content: readonly { type: string; text?: string }[]; errorMessage?: string }

type ModelRegistry<S> = {
  find(provider: string, modelId: string): object | undefined
  hasConfiguredAuth(model: object): boolean
  streamSimple(
    model: object,
    context: { messages: { role: 'user'; content: string; timestamp: number }[] },
    options: { maxTokens: number; signal: S },
  ): { result(): Promise<ModelReply> }
}

type Repaint = { requestRender(): void }

type Widget = { render(width: number): string[]; invalidate(): void }

export type PiContext<S extends Signal = Signal> = {
  mode: string
  cwd: string
  ui: {
    setWidget(key: string, content: (tui: Repaint, theme: BandTheme) => Widget, options: { placement: 'aboveEditor' }): void
    notify(message: string, type: 'warning'): void
  }
  sessionManager: { getBranch(): readonly PiEntry[] }
  modelRegistry: ModelRegistry<S>
  isIdle(): boolean
}

export type Pi<S extends Signal = Signal> = {
  on(event: string, handler: (event: never, ctx: PiContext<S>) => unknown): unknown
  appendEntry(customType: string, data: DevPhaseState): void
  setSessionName(name: string): void
  getSessionName(): string | undefined
  getCommands(): readonly PiCommand[]
}

export type PiEvents = {
  session_start: object
  session_tree: object
  session_shutdown: object
  message_end: { message: unknown }
  agent_start: object
  tool_result: { toolName: string; input: Record<string, unknown>; isError: boolean }
  user_bash: { command: string }
  turn_end: object
  agent_end: { messages: readonly unknown[] }
  agent_settled: { aborted: boolean }
}

type Ask = { generation: number; serial: number }

type Reply = { kind: 'answered'; text: string } | { kind: 'failed'; reason: string; isRetryable: boolean } | { kind: 'unavailable' }

type Outcome = 'settled' | 'retry'

const WIDGET = 'dev-phase'
const DIGEST_ENTRIES = 400

// Same picks as bin/extraction.py; the agent-models skill updates both.
const MODELS = [
  ['openrouter', 'google/gemini-2.5-flash-lite'],
  ['openrouter', 'google/gemini-3.1-flash-lite'],
] as const

const EMPTY: DevPhaseState = { record: null, topic: null }

const withRecord = (current: DevPhaseRecord | null, next: DevPhaseRecord | null): DevPhaseRecord | null =>
  current !== null && next !== null && current.phase === next.phase && current.source === next.source ? current : next

const replyText = (reply: ModelReply): string =>
  reply.content
    .filter(block => block.type === 'text')
    .map(block => block.text ?? '')
    .join('')

export const createDevPhase =
  <S extends Signal>(deps: Deps<S>) =>
  (pi: Pi<S>): void => {
    const shutdown = deps.abortController()
    let ctx: PiContext<S> | undefined
    let isActive = false
    let isDisposed = false
    let state = EMPTY
    let saved: string | undefined
    let isUnsaved = false
    let lastTitle: string | undefined
    let skillOf: SkillOf = () => undefined
    let repaint: Repaint | undefined
    let isSkillTurn = false
    let isDirty = false
    let isClassifying = false
    let hasWarned = false
    let lastRunAnswered = false
    let generation = 0
    let serial = 0
    let queued: Ask | undefined
    let idleTimer: unknown

    const on = <K extends keyof PiEvents>(
      event: K,
      handler: (e: PiEvents[K], c: PiContext<S>) => void | Promise<void>,
    ): void => {
      pi.on(event, handler as (e: never, c: PiContext<S>) => unknown)
    }

    const changed = (): void => {
      isUnsaved = true
      repaint?.requestRender()
    }

    const applyTitle = (): void => {
      const topic = state.topic
      if (topic === null) return
      const title = retitle({ ...topic, titled: topic.titled ?? lastTitle }, pi.getSessionName())
      if (title === undefined) return
      pi.setSessionName(title)
      lastTitle = title
      state = { ...state, topic: { ...topic, titled: title } }
      isUnsaved = true
    }

    const persist = (): void => {
      if (!isUnsaved) return
      isUnsaved = false
      const json = JSON.stringify(state)
      if (json === saved) return
      pi.appendEntry(ENTRY_TYPE, state)
      saved = json
    }

    const commit = (): void => {
      if (isDisposed || !isActive) return
      try {
        applyTitle()
        persist()
      } catch (error) {
        deps.debug(`saving failed: ${String(error)}`)
      }
    }

    const setPhase = (phase: DevPhase, source: DevPhaseSource): void => {
      const record = withRecord(state.record, { phase, at: deps.now(), source })
      if (record === state.record) return
      state = { ...state, record }
      changed()
    }

    const markDirty = (): void => {
      isDirty = true
      generation += 1
    }

    const onSkill = (skill: string | undefined): void => {
      if (skill === undefined) return
      const phase = phaseOfSkill(skill, state.record?.phase)
      if (phase === undefined) return
      isSkillTurn = true
      generation += 1
      setPhase(phase, 'skill')
    }

    const cancelIdle = (): void => {
      if (idleTimer === undefined) return
      deps.clearTimer(idleTimer)
      idleTimer = undefined
    }

    const askModel = async (context: PiContext<S>, prompt: string): Promise<Reply> => {
      let failure: Reply = { kind: 'unavailable' }
      for (const [provider, id] of MODELS) {
        const model = context.modelRegistry.find(provider, id)
        if (model === undefined || !context.modelRegistry.hasConfiguredAuth(model)) continue
        const reply = await context.modelRegistry
          .streamSimple(
            model,
            { messages: [{ role: 'user', content: prompt, timestamp: deps.now() }] },
            { maxTokens: MAX_TOKENS, signal: deps.deadline(shutdown.signal, MODEL_TIMEOUT_MS) },
          )
          .result()
        switch (reply.stopReason) {
          case 'stop':
          case 'length':
            return { kind: 'answered', text: replyText(reply) }
          case 'aborted':
            if (shutdown.signal.aborted) return { kind: 'failed', reason: 'shut down', isRetryable: false }
            failure = { kind: 'failed', reason: 'timed out', isRetryable: true }
            break
          default:
            failure = { kind: 'failed', reason: reply.errorMessage ?? reply.stopReason, isRetryable: true }
        }
      }
      return failure
    }

    const applyVerdict = (ask: Ask, text: string): void => {
      const next = verdictState(text, state, deps.now(), 'log')
      if (next === undefined) return deps.debug(`unparseable verdict: ${text.slice(0, 200)}`)
      if (ask.generation !== generation || isDisposed) return
      state = { topic: next.topic, record: withRecord(state.record, next.record) }
      changed()
      if (ctx?.isIdle() === true) commit()
    }

    const classify = async (ask: Ask): Promise<Outcome> => {
      const context = ctx
      if (context === undefined) return 'settled'
      const entries = context.sessionManager.getBranch().slice(-DIGEST_ENTRIES)
      const rows = digest(toDigestMessages(entries, skillOf))
      if (rows === '') return 'settled'
      const reply = await askModel(context, digestPrompt(rows, state.topic))
      if (isDisposed) return 'settled'
      switch (reply.kind) {
        case 'answered':
          applyVerdict(ask, reply.text)
          return 'settled'
        case 'failed':
          deps.debug(`log classification unanswered: ${reply.reason}`)
          return reply.isRetryable ? 'retry' : 'settled'
        case 'unavailable':
          if (!hasWarned) {
            hasWarned = true
            context.ui.notify(`dev-phase: no credentials for ${MODELS[0].join('/')}; phase labels are off`, 'warning')
          }
          return 'settled'
      }
    }

    const runClassification = (ask: Ask): void => {
      if (isDisposed) return
      if (ask.serial !== serial) {
        isDirty = true
        return
      }
      if (isClassifying) {
        queued = ask
        return
      }
      isClassifying = true
      void classify(ask)
        .then(outcome => {
          if (outcome === 'retry' && !isDisposed) isDirty = true
        })
        .catch(error => deps.debug(`classification failed: ${String(error)}`))
        .finally(() => {
          isClassifying = false
          const next = queued
          queued = undefined
          if (next !== undefined) runClassification(next)
        })
    }

    const hydrate = (branch: readonly PiEntry[], latest: DevPhaseState | undefined): void => {
      state = latest ?? EMPTY
      saved = latest === undefined ? undefined : JSON.stringify(latest)
      isUnsaved = false
      lastTitle = latestTitle(branch) ?? lastTitle
      repaint?.requestRender()
    }

    on('session_start', (e, c) => {
      ctx = c
      isActive = c.mode === 'tui'
      if (!isActive) return
      skillOf = skillResolver(pi.getCommands(), { cwd: c.cwd, home: deps.home })
      const branch = c.sessionManager.getBranch()
      const latest = latestState(branch)
      hydrate(branch, latest)
      c.ui.setWidget(
        WIDGET,
        (tui, theme) => {
          repaint = tui
          return {
            render: width => [deps.truncate(bandLine(theme, state.record, state.topic), width)],
            invalidate: () => undefined,
          }
        },
        { placement: 'aboveEditor' },
      )
      commit()
      if (latest === undefined && hasHistory(branch)) runClassification({ generation, serial })
    })

    on('session_tree', (e, c) => {
      ctx = c
      if (!isActive) return
      cancelIdle()
      generation += 1
      isSkillTurn = false
      isDirty = false
      const branch = c.sessionManager.getBranch()
      const latest = latestState(branch)
      hydrate(branch, latest)
      if (latest === undefined && hasHistory(branch)) runClassification({ generation, serial })
    })

    on('session_shutdown', () => {
      commit()
      isDisposed = true
      cancelIdle()
      shutdown.abort()
      repaint = undefined
    })

    on('message_end', e => {
      if (isActive) onSkill(skillFromUserMessage(e.message))
    })

    on('agent_start', () => {
      serial += 1
      lastRunAnswered = false
      if (idleTimer !== undefined) isDirty = true
      cancelIdle()
    })

    on('tool_result', e => {
      if (!isActive) return
      const { path, command } = e.input
      switch (e.toolName) {
        case 'read':
          if (!e.isError && typeof path === 'string') onSkill(skillOf(path))
          return
        case 'edit':
        case 'write': {
          if (e.isError || typeof path !== 'string') return
          markDirty()
          if (isSkillTurn) return
          const phase = provisionalPhase(state.record?.phase, path)
          if (phase !== undefined) setPhase(phase, 'edit')
          return
        }
        case 'bash':
          if (typeof command !== 'string') return
          if (!e.isError) onSkill(skillFromCommand(command, skillOf))
          if (isCheckpoint(command)) markDirty()
          return
      }
    })

    on('user_bash', e => {
      if (isActive && isCheckpoint(e.command)) markDirty()
    })

    on('turn_end', () => commit())

    on('agent_end', e => {
      lastRunAnswered = lastAssistantStop(e.messages) === 'stop'
    })

    on('agent_settled', e => {
      commit()
      if (!isActive) return
      if (isSkillTurn) {
        isSkillTurn = false
        isDirty = false
        return
      }
      const isUnclassified = saved === undefined && state.record === null
      if (!(isDirty || isUnclassified) || e.aborted || !lastRunAnswered) return
      isDirty = false
      const ask = { generation, serial }
      idleTimer = deps.setTimer(() => {
        idleTimer = undefined
        runClassification(ask)
      }, IDLE_MS)
    })
  }
