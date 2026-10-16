import { asRecord, asTopic } from '../core/phase'
import type { DevPhaseState, DigestMessage, DigestToolUse } from '../core/phase'

export type PiEntry = { type: string; customType?: string; data?: unknown; message?: unknown }

export type PiCommand = { name: string; source: string; sourceInfo?: { path?: string } }

export type SkillOf = (path: string) => string | undefined

export const ENTRY_TYPE = 'dev-phase'

const SKILL_COMMAND = 'skill:'

type Fields = Record<string, unknown>

const isFields = (value: unknown): value is Fields => typeof value === 'object' && value !== null

const normalisePath = (path: string, cwd: string, home: string): string => {
  const bare = path.startsWith('@') ? path.slice(1) : path
  const expanded = bare === '~' ? home : bare.startsWith('~/') ? `${home}${bare.slice(1)}` : bare
  const absolute = expanded.startsWith('/') ? expanded : `${cwd}/${expanded}`
  const parts: string[] = []
  for (const part of absolute.split('/')) {
    if (part === '' || part === '.') continue
    if (part === '..') parts.pop()
    else parts.push(part)
  }
  return `/${parts.join('/')}`
}

export const skillResolver = (
  commands: readonly PiCommand[],
  location: { cwd: string; home: string },
): SkillOf => {
  const resolve = (path: string) => normalisePath(path, location.cwd, location.home)
  const index = new Map(
    commands.flatMap(({ name, source, sourceInfo }) =>
      source === 'skill' && name.startsWith(SKILL_COMMAND) && typeof sourceInfo?.path === 'string'
        ? [[resolve(sourceInfo.path), name.slice(SKILL_COMMAND.length)] as const]
        : [],
    ),
  )
  return path => index.get(resolve(path))
}

const READERS = new Set(['cat', 'head', 'tail', 'sed', 'awk', 'less', 'more', 'bat', 'nl'])
const SKILL_PATH = /[^\s'"`;|&()<>]*SKILL\.md\b/g

export const skillFromCommand = (command: string, skillOf: SkillOf): string | undefined =>
  command
    .split(/[;&|]+/)
    .filter(segment => READERS.has(/^[\s(]*(\S+)/.exec(segment)?.[1] ?? ''))
    .flatMap(segment => segment.match(SKILL_PATH) ?? [])
    .map(skillOf)
    .find(name => name !== undefined)

const textOf = (content: unknown): string => {
  if (typeof content === 'string') return content
  if (!Array.isArray(content)) return ''
  return content
    .filter((block): block is Fields => isFields(block) && block.type === 'text' && typeof block.text === 'string')
    .map(block => block.text)
    .join('\n')
}

const SKILL_BLOCK = /^<skill name="([^"]+)"/
const SKILL_END = '\n</skill>'

const expandedSkill = (text: string): { skill: string; rest: string } | undefined => {
  const skill = SKILL_BLOCK.exec(text)?.[1]
  const end = text.indexOf(SKILL_END)
  return skill === undefined || end === -1 ? undefined : { skill, rest: text.slice(end + SKILL_END.length).trim() }
}

export const skillFromUserMessage = (message: unknown): string | undefined =>
  isFields(message) && message.role === 'user' ? expandedSkill(textOf(message.content))?.skill : undefined

const userMessage = (content: unknown): DigestMessage => {
  const text = textOf(content)
  const expanded = expandedSkill(text)
  if (expanded === undefined) return { role: 'user', text, toolUses: [] }
  return { role: 'user', text: expanded.rest, toolUses: [{ tool: 'Skill', input: { skill: expanded.skill } }] }
}

const canonicalTool = (name: string): string => `${name.charAt(0).toUpperCase()}${name.slice(1)}`

const toolUse = (name: string, input: Fields, skillOf: SkillOf): DigestToolUse => {
  const skill = name === 'read' && typeof input.path === 'string' ? skillOf(input.path) : undefined
  return skill === undefined ? { tool: canonicalTool(name), input } : { tool: 'Skill', input: { skill } }
}

const nestedUses = (entries: readonly PiEntry[]): Map<string, readonly Fields[]> =>
  new Map(
    entries.flatMap(({ type, message }) => {
      if (type !== 'message' || !isFields(message) || message.role !== 'toolResult') return []
      const calls = isFields(message.nestedCalls) ? message.nestedCalls.calls : undefined
      return typeof message.toolCallId === 'string' && Array.isArray(calls)
        ? [[message.toolCallId, calls.filter(isFields)] as const]
        : []
    }),
  )

const callUse = (call: Fields, skillOf: SkillOf): DigestToolUse[] =>
  typeof call.name === 'string' ? [toolUse(call.name, isFields(call.arguments) ? call.arguments : {}, skillOf)] : []

const assistantMessage = (
  content: unknown,
  nested: ReadonlyMap<string, readonly Fields[]>,
  skillOf: SkillOf,
): DigestMessage => {
  const blocks = Array.isArray(content) ? content.filter(isFields) : []
  const toolUses = blocks
    .filter(block => block.type === 'toolCall')
    .flatMap(block => [
      ...callUse(block, skillOf),
      ...(typeof block.id === 'string' ? (nested.get(block.id) ?? []) : []).flatMap(call => callUse(call, skillOf)),
    ])
  return { role: 'assistant', text: textOf(content), toolUses }
}

export const toDigestMessages = (entries: readonly PiEntry[], skillOf: SkillOf): DigestMessage[] => {
  const nested = nestedUses(entries)
  return entries.flatMap(({ type, message }): DigestMessage[] => {
    if (type !== 'message' || !isFields(message)) return []
    switch (message.role) {
      case 'user':
        return [userMessage(message.content)]
      case 'assistant':
        return [assistantMessage(message.content, nested, skillOf)]
      case 'bashExecution':
        return typeof message.command === 'string' && message.excludeFromContext !== true
          ? [{ role: 'user', text: '', toolUses: [{ tool: 'Bash', input: { command: message.command } }] }]
          : []
      default:
        return []
    }
  })
}

const asState = (data: unknown): DevPhaseState | undefined => {
  if (!isFields(data)) return undefined
  const record = data.record === null ? null : asRecord(data.record)
  const topic = data.topic === null ? null : asTopic(data.topic)
  return record === undefined || topic === undefined ? undefined : { record, topic }
}

const savedStates = (entries: readonly PiEntry[]): DevPhaseState[] =>
  entries
    .filter(entry => entry.type === 'custom' && entry.customType === ENTRY_TYPE)
    .map(entry => asState(entry.data))
    .filter(state => state !== undefined)

export const latestState = (entries: readonly PiEntry[]): DevPhaseState | undefined => savedStates(entries).at(-1)

export const latestTitle = (entries: readonly PiEntry[]): string | undefined =>
  savedStates(entries)
    .map(state => state.topic?.titled)
    .filter(title => title !== undefined)
    .at(-1)

export const hasHistory = (entries: readonly PiEntry[]): boolean =>
  entries.some(
    ({ type, message }) =>
      type === 'message' && isFields(message) && (message.role === 'user' || message.role === 'assistant'),
  )

export const lastAssistantStop = (messages: readonly unknown[]): string | undefined => {
  const last = messages.filter(message => isFields(message) && message.role === 'assistant').at(-1)
  return isFields(last) && typeof last.stopReason === 'string' ? last.stopReason : undefined
}
