import { atom, read, update } from 'claude-code'
import type { EngineInterface, Register } from 'claude-code'

import type { DevPhase, DevPhaseRecord, DevPhaseSource, DevTopic } from '../types'
import {
  asRecord,
  asTopic,
  bareName,
  digest,
  digestPrompt,
  forkPrompt,
  isCheckRun,
  isGitCommit,
  parseFeature,
  parseVerdict,
  phaseColor,
  phaseOfSkill,
  provisionalPhase,
  retitle,
  staleKeys,
  storeKey,
  topicKey,
} from './phase'

type Dollar = EngineInterface
type Ask = { sessionId: string; generation: number; serial: number }
type TurnContext = { previous: DevPhaseRecord | null; topic: DevTopic | null; answer: string }
type Pending = { ask: Ask; turn: TurnContext }
type Outcome = 'settled' | 'retry'
type Tracker = {
  isSkillTurn: boolean
  isDirty: boolean
  isForking: boolean
  queued: Pending | undefined
  generation: number
  serial: number
  subagentSkills: Map<string, number>
  classifiedFromLog: string | undefined
}

const current = atom({ plugin: 'dev-phase', key: 'current' } as const, null)
const topicAtom = atom({ plugin: 'dev-phase', key: 'topic' } as const, null)

const KEPT_SESSIONS = 300
const IDLE_MS = 30_000

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

async function save($: Dollar, sessionId: string, record: DevPhaseRecord | null): Promise<void> {
  await put($, storeKey(sessionId), record)
  if (await isCurrentSession($, sessionId)) await update($, current, () => record)
}

async function saveTopic($: Dollar, sessionId: string, topic: DevTopic | null): Promise<void> {
  if (topic === null) await $.store.delete(topicKey(sessionId))
  else await put($, topicKey(sessionId), topic)
  if (await isCurrentSession($, sessionId)) await update($, topicAtom, () => topic)
}

async function storedTopic($: Dollar, sessionId: string): Promise<DevTopic | undefined> {
  return asTopic(await $.store.get(topicKey(sessionId)))
}

async function nameTopic($: Dollar, sessionId: string, name: string | null): Promise<void> {
  const known = await storedTopic($, sessionId)
  if (name === null) {
    if (known !== undefined) await saveTopic($, sessionId, null)
    return
  }
  if (known?.name === name) return
  await saveTopic($, sessionId, { ...known, name, at: await $.clock.now() })
}

async function setPhase($: Dollar, phase: DevPhase, source: DevPhaseSource): Promise<void> {
  await save($, await $.session.id(), { phase, at: await $.clock.now(), source })
}

async function prune($: Dollar, sessionId: string): Promise<void> {
  const stale = staleKeys(await $.store.keys(), KEPT_SESSIONS, sessionId)
  await Promise.all(stale.map(key => $.store.delete(key)))
}

async function applyVerdict($: Dollar, tracker: Tracker, ask: Ask, text: string, source: DevPhaseSource): Promise<void> {
  const verdict = parseVerdict(text)
  if (verdict === undefined) return debug($, `unparseable verdict: ${text.slice(0, 200)}`)
  if (ask.generation !== tracker.generation) return
  const feature = parseFeature(text)
  if (feature !== undefined) await nameTopic($, ask.sessionId, feature)
  await save($, ask.sessionId, verdict === null ? null : { phase: verdict, at: await $.clock.now(), source })
}

async function classifyFromLog($: Dollar, tracker: Tracker, ask: Ask): Promise<void> {
  const rows = digest(await $.session.messages())
  if (rows === '') return
  const reply = await $.model.complete({
    model: 'haiku',
    prompt: digestPrompt(rows, (await storedTopic($, ask.sessionId)) ?? null),
    maxTokens: 60,
    effort: 'low',
    timeoutMs: 20_000,
  })
  if (reply.isAnswered) return applyVerdict($, tracker, ask, reply.text, 'log')
  debug($, `log classification unanswered: ${reply.reason}`)
}

async function classifyTurn($: Dollar, tracker: Tracker, { ask, turn }: Pending): Promise<Outcome> {
  const reply = await $.model.fork({ prompt: forkPrompt(turn.previous, turn.topic, turn.answer) })
  if (reply.isAnswered) {
    debug($, `fork read ${reply.usage.cache_read_input_tokens} cached tokens`)
    await applyVerdict($, tracker, ask, reply.text, 'fork')
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
  const stored = await touch($, storeKey(sessionId))
  const topic = asTopic(await touch($, topicKey(sessionId)))
  await update($, current, () => asRecord(stored) ?? null)
  await update($, topicAtom, () => topic ?? null)
  if (stored !== undefined || !hasHistory || tracker.classifiedFromLog === sessionId) return
  tracker.classifiedFromLog = sessionId
  classifyFromLogLater($, tracker, { sessionId, generation: tracker.generation, serial: tracker.serial })
}

function markDirty(tracker: Tracker): void {
  tracker.isDirty = true
  tracker.generation += 1
}

function skillCount(tracker: Tracker, skill: string): number {
  return tracker.subagentSkills.get(bareName(skill)) ?? 0
}

export const register: Register = on => {
  const tracker: Tracker = {
    isSkillTurn: false,
    isDirty: false,
    isForking: false,
    queued: undefined,
    generation: 0,
    serial: 0,
    subagentSkills: new Map(),
    classifiedFromLog: undefined,
  }

  const resetTurn = (): void => {
    tracker.isSkillTurn = false
    tracker.isDirty = false
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
    const phase = phaseOfSkill(e.skill, (await read($, current))?.phase)
    if (phase !== undefined) {
      tracker.isSkillTurn = true
      tracker.generation += 1
      await setPhase($, phase, 'skill')
    }
    return next(e)
  })

  on('tool.call', { tool: ['Edit', 'Write', 'NotebookEdit'] }, async ($, e, next) => {
    const ran = await next(e)
    if (ran.deny !== undefined || ran.isError === true) return ran
    markDirty(tracker)
    if (tracker.isSkillTurn) return ran
    const path = e.tool === 'NotebookEdit' ? e.notebook_path : e.file_path
    const phase = provisionalPhase((await read($, current))?.phase, path)
    if (phase !== undefined) await setPhase($, phase, 'edit')
    return ran
  })

  on('tool.call', { tool: 'Bash' }, async ($, e, next) => {
    const ran = await next(e)
    if (isGitCommit(e.command) || isCheckRun(e.command)) markDirty(tracker)
    return ran
  })

  on('turn.complete', async ($, e, next) => {
    const done = await next(e)
    if (e.agentId !== undefined) return done
    if (tracker.isSkillTurn) {
      resetTurn()
      return done
    }
    if (!tracker.isDirty || e.reason !== 'answer') return done
    tracker.isDirty = false
    const pending: Pending = {
      ask: { sessionId: await $.session.id(), generation: tracker.generation, serial: tracker.serial },
      turn: { previous: await read($, current), topic: await read($, topicAtom), answer: e.answer },
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
        resetTurn()
        await update($, current, () => null)
        await update($, topicAtom, () => null)
        break
      case 'resume':
        resetTurn()
        await hydrate($, tracker, e.session_id, true)
        break
      case 'fork': {
        resetTurn()
        const inherited = await read($, current)
        const inheritedTopic = await read($, topicAtom)
        if (inheritedTopic !== null) {
          await put($, topicKey(e.session_id), { name: inheritedTopic.name, at: inheritedTopic.at })
        }
        if (inherited === null) await hydrate($, tracker, e.session_id, true)
        else await put($, storeKey(e.session_id), inherited)
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
    const record = await read($, current)
    const topic = await read($, topicAtom)
    const { Box, Text } = $.ui.resolve(e)
    const feature =
      topic === null ? null : (
        <Text dimColor wrap="truncate-end">
          {` · ${topic.name}`}
        </Text>
      )
    if (record === null) {
      return (
        <Box width={e.props.bodyColumns}>
          <Text dimColor>● no phase yet</Text>
          {feature}
        </Box>
      )
    }
    const isProvisional = record.source === 'edit'
    return (
      <Box width={e.props.bodyColumns}>
        <Text color={phaseColor(record.phase)} dimColor={isProvisional}>
          ●{' '}
        </Text>
        <Text bold dimColor={isProvisional}>
          {record.phase}
        </Text>
        {feature}
      </Box>
    )
  })
}
