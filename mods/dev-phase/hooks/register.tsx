import { atom, read, update } from 'claude-code'
import type { EngineInterface, Register } from 'claude-code'

import type { DevCheck, DevChecks, DevState, DevTopic } from '../types'
import {
  asStoredChecks,
  asTopic,
  bareName,
  checkItems,
  checksKey,
  digest,
  digestPrompt,
  forkPrompt,
  IDLE_MS,
  isCheckpoint,
  MAX_TOKENS,
  MODEL_TIMEOUT_MS,
  retitle,
  sameChecks,
  skillEffect,
  staleKeys,
  topicKey,
  UNCHECKED,
  unearnedChecks,
  unknownStale,
  verdictState,
  withCheck,
  withoutChecks,
} from '../core/checklist'

type Dollar = EngineInterface
type Ask = { sessionId: string; generation: number; serial: number; held: readonly DevCheck[] }
type TurnContext = DevState & { answer: string }
type Pending = { ask: Ask; turn: TurnContext }
type Outcome = 'settled' | 'retry'
type Tracker = {
  isDirty: boolean
  isForking: boolean
  queued: Pending | undefined
  generation: number
  serial: number
  subagentSkills: Map<string, number>
  classifiedFromLog: string | undefined
  turnChecks: Map<DevCheck, boolean>
}

const checksAtom = atom({ plugin: 'dev-phase', key: 'checks' } as const, UNCHECKED)
const topicAtom = atom({ plugin: 'dev-phase', key: 'topic' } as const, null)

const KEPT_SESSIONS = 300

function debug($: Dollar, text: string): void {
  $.ui.log(`dev-phase: ${text}`, { to: 'debug' })
}

async function isCurrentSession($: Dollar, sessionId: string): Promise<boolean> {
  return (await $.session.id()) === sessionId
}

async function put($: Dollar, key: string, value: unknown): Promise<void> {
  await $.store.delete(key)
  await $.store.set(key, value)
}

async function touch($: Dollar, key: string): Promise<unknown> {
  const value = await $.store.get(key)
  if (value !== undefined) await put($, key, value)
  return value
}

async function saveChecks($: Dollar, sessionId: string, checks: DevChecks): Promise<void> {
  await put($, checksKey(sessionId), checks)
  if (await isCurrentSession($, sessionId)) await update($, checksAtom, () => checks)
}

async function saveTopic($: Dollar, sessionId: string, topic: DevTopic | null): Promise<void> {
  if (topic === null) await $.store.delete(topicKey(sessionId))
  else await put($, topicKey(sessionId), topic)
  if (await isCurrentSession($, sessionId)) await update($, topicAtom, () => topic)
}

async function storedChecks($: Dollar, sessionId: string): Promise<DevChecks> {
  return asStoredChecks(await $.store.get(checksKey(sessionId))) ?? UNCHECKED
}

async function storedTopic($: Dollar, sessionId: string): Promise<DevTopic | undefined> {
  return asTopic(await $.store.get(topicKey(sessionId)))
}

async function storedState($: Dollar, sessionId: string): Promise<DevState> {
  return { checks: await storedChecks($, sessionId), topic: (await storedTopic($, sessionId)) ?? null }
}

async function prune($: Dollar, sessionId: string): Promise<void> {
  const stale = staleKeys(await $.store.keys(), KEPT_SESSIONS, sessionId)
  await Promise.all(stale.map(key => $.store.delete(key)))
}

async function applyVerdict($: Dollar, tracker: Tracker, ask: Ask, text: string): Promise<void> {
  const known = await storedState($, ask.sessionId)
  const next = verdictState(text, known, await $.clock.now(), ask.held)
  if (next === undefined) return debug($, `unparseable verdict: ${text.slice(0, 200)}`)
  const unknown = unknownStale(text)
  if (unknown.length > 0) debug($, `unknown stale checks: ${unknown.join(', ')}`)
  if (ask.generation !== tracker.generation) return
  await saveChecks($, ask.sessionId, next.checks)
  if (next.topic !== known.topic) await saveTopic($, ask.sessionId, next.topic)
}

async function classifyFromLog($: Dollar, tracker: Tracker, ask: Ask): Promise<void> {
  const rows = digest(await $.session.messages())
  if (rows === '') return
  const reply = await $.model.complete({
    model: 'haiku',
    prompt: digestPrompt(await storedState($, ask.sessionId), rows),
    maxTokens: MAX_TOKENS,
    effort: 'low',
    timeoutMs: MODEL_TIMEOUT_MS,
  })
  if (reply.isAnswered) return applyVerdict($, tracker, ask, reply.text)
  debug($, `log classification unanswered: ${reply.reason}`)
}

async function classifyTurn($: Dollar, tracker: Tracker, { ask, turn }: Pending): Promise<Outcome> {
  const reply = await $.model.fork({ prompt: forkPrompt(turn, turn.answer) })
  if (reply.isAnswered) {
    debug($, `fork read ${reply.usage.cache_read_input_tokens} cached tokens`)
    await applyVerdict($, tracker, ask, reply.text)
    return 'settled'
  }
  switch (reply.reason) {
    case 'nothing-to-fork':
      await classifyFromLog($, tracker, ask)
      return 'settled'
    case 'api-error':
    case 'aborted':
      debug($, `fork unanswered: ${reply.reason}`)
      return 'retry'
    case 'empty-reply':
      debug($, 'fork gave an empty reply')
      return 'settled'
    default:
      debug($, `fork unanswered: ${String((reply as { reason: unknown }).reason)}`)
      return 'settled'
  }
}

function runClassification($: Dollar, tracker: Tracker, pending: Pending): void {
  if (pending.ask.serial !== tracker.serial) {
    tracker.isDirty = true
    return
  }
  if (tracker.isForking) {
    tracker.queued = pending
    return
  }
  tracker.isForking = true
  void classifyTurn($, tracker, pending)
    .then(async outcome => {
      if (outcome === 'retry' && (await isCurrentSession($, pending.ask.sessionId))) tracker.isDirty = true
    })
    .catch(error => debug($, `classification failed: ${String(error)}`))
    .finally(() => {
      tracker.isForking = false
      const queued = tracker.queued
      tracker.queued = undefined
      if (queued !== undefined) runClassification($, tracker, queued)
    })
}

function classifyFromLogLater($: Dollar, tracker: Tracker, ask: Ask): void {
  $.clock.after(1, () => {
    void classifyFromLog($, tracker, ask).catch(error => debug($, `classification failed: ${String(error)}`))
  })
}

async function hydrate($: Dollar, tracker: Tracker, sessionId: string, hasHistory: boolean): Promise<void> {
  const stored = await touch($, checksKey(sessionId))
  const topic = asTopic(await touch($, topicKey(sessionId)))
  await update($, checksAtom, () => asStoredChecks(stored) ?? UNCHECKED)
  await update($, topicAtom, () => topic ?? null)
  if (stored !== undefined || !hasHistory || tracker.classifiedFromLog === sessionId) return
  tracker.classifiedFromLog = sessionId
  classifyFromLogLater($, tracker, { sessionId, generation: tracker.generation, serial: tracker.serial, held: [] })
}

function markDirty(tracker: Tracker): void {
  tracker.isDirty = true
  tracker.generation += 1
}

function resetTurn(tracker: Tracker): void {
  tracker.isDirty = false
  tracker.turnChecks = new Map()
}

function skillCount(tracker: Tracker, skill: string): number {
  return tracker.subagentSkills.get(bareName(skill)) ?? 0
}

export const register: Register = on => {
  const tracker: Tracker = {
    isDirty: false,
    isForking: false,
    queued: undefined,
    generation: 0,
    serial: 0,
    subagentSkills: new Map(),
    classifiedFromLog: undefined,
    turnChecks: new Map(),
  }

  on('turn.start', async ($, e, next) => {
    tracker.serial += 1
    return next(e)
  })

  on('tool.call', { tool: 'Skill' }, async ($, e, next) => {
    if (e.agentId === undefined) return next(e)
    tracker.subagentSkills.set(bareName(e.skill), skillCount(tracker, e.skill) + 1)
    try {
      return await next(e)
    } finally {
      tracker.subagentSkills.set(bareName(e.skill), skillCount(tracker, e.skill) - 1)
    }
  })

  on('skill.prompt', async ($, e, next) => {
    if (skillCount(tracker, e.skill) > 0) return next(e)
    const { check, isDirtying } = skillEffect(e.skill)
    if (isDirtying) markDirty(tracker)
    if (check === undefined) return next(e)
    const checks = await read($, checksAtom)
    if (!tracker.turnChecks.has(check)) tracker.turnChecks.set(check, checks[check])
    await saveChecks($, await $.session.id(), withCheck(checks, check))
    return next(e)
  })

  on('tool.call', { tool: ['Edit', 'Write', 'NotebookEdit'] }, async ($, e, next) => {
    const ran = await next(e)
    if (ran.deny === undefined && ran.isError !== true) markDirty(tracker)
    return ran
  })

  on('tool.call', { tool: 'Bash' }, async ($, e, next) => {
    const ran = await next(e)
    if (isCheckpoint(e.command)) markDirty(tracker)
    return ran
  })

  on('turn.complete', async ($, e, next) => {
    const done = await next(e)
    if (e.agentId !== undefined) return done
    const ran = tracker.turnChecks
    tracker.turnChecks = new Map()
    const sessionId = await $.session.id()
    if (e.reason !== 'answer') {
      const unearned = unearnedChecks(ran)
      if (unearned.length > 0) await saveChecks($, sessionId, withoutChecks(await read($, checksAtom), unearned))
      return done
    }
    if (!tracker.isDirty) return done
    tracker.isDirty = false
    const pending: Pending = {
      ask: { sessionId, generation: tracker.generation, serial: tracker.serial, held: [...ran.keys()] },
      turn: { checks: await read($, checksAtom), topic: await read($, topicAtom), answer: e.answer },
    }
    $.clock.after(IDLE_MS, () => runClassification($, tracker, pending))
    return done
  })

  on('classic.UserPromptSubmit', async ($, e, next) => {
    const result = await next(e)
    if (result.sessionTitle !== undefined) return result
    const topic = await storedTopic($, e.session_id)
    const title = retitle(topic, e.session_title)
    if (topic === undefined || title === undefined) return result
    debug($, `retitling from ${JSON.stringify(e.session_title)} to ${JSON.stringify(title)}`)
    await saveTopic($, e.session_id, { ...topic, titled: title })
    return { ...result, sessionTitle: title }
  })

  on('session.start', async ($, e, next) => {
    const sessionId = await $.session.id()
    await hydrate($, tracker, sessionId, (await $.session.turns()) > 0)
    await prune($, sessionId)
    return next(e)
  })

  on('classic.SessionStart', async ($, e, next) => {
    switch (e.source) {
      case 'clear':
        resetTurn(tracker)
        await update($, checksAtom, () => UNCHECKED)
        await update($, topicAtom, () => null)
        break
      case 'resume':
        resetTurn(tracker)
        await hydrate($, tracker, e.session_id, true)
        break
      case 'fork': {
        resetTurn(tracker)
        const inherited = await read($, checksAtom)
        const inheritedTopic = await read($, topicAtom)
        if (inheritedTopic === null && sameChecks(inherited, UNCHECKED)) {
          await hydrate($, tracker, e.session_id, true)
          break
        }
        if (inheritedTopic !== null) {
          await put($, topicKey(e.session_id), { name: inheritedTopic.name, at: inheritedTopic.at })
        }
        await put($, checksKey(e.session_id), inherited)
        break
      }
      case 'startup':
      case 'compact':
        break
      default:
        debug($, `unknown SessionStart source: ${String(e.source)}`)
    }
    return next(e)
  })

  on('ui.render', { component: 'AbovePrompt' }, async ($, e, next) => {
    if (e.props.hasSurvey) return next(e)
    const { Box, Text } = $.ui.resolve(e)
    return (
      <Box width={e.props.bodyColumns} gap={2}>
        {checkItems(await read($, checksAtom)).map(({ check, mark, color }) => (
          <Box key={check}>
            <Text color={color}>{`${mark} `}</Text>
            <Text>{check}</Text>
          </Box>
        ))}
      </Box>
    )
  })
}
