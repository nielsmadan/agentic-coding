import type { DevCheck, DevChecks, DevState, DevTopic } from '../types'

export type { DevState } from '../types'

export type DigestToolUse = { tool: string; input: Readonly<Record<string, unknown>> }

export type DigestMessage = { role: 'user' | 'assistant'; text: string; toolUses: readonly DigestToolUse[] }

export const UNCHECKED: DevChecks = { 'code-review': false, 'findings-addressed': false, qa: false, 'qa-tour': false }

export const CHECKS = Object.keys(UNCHECKED) as readonly DevCheck[]

const ADDRESSED: DevCheck = 'findings-addressed'

const SKILL_CHECKS = CHECKS.filter(check => check !== ADDRESSED)

export type CheckItem = { check: DevCheck; mark: '✓' | '✗'; color: 'success' | 'error' }

export const checkItems = (checks: DevChecks): CheckItem[] =>
  CHECKS.map(check => (checks[check] ? { check, mark: '✓', color: 'success' } : { check, mark: '✗', color: 'error' }))

const NEW_WORK_SKILLS = new Set([
  'plan',
  'longshot',
  'brainstorm',
  'brainstorming',
  'writing-plans',
  'blind-spots',
  'review-plan',
  'ideation',
])

export const bareName = (skill: string): string => skill.slice(skill.lastIndexOf(':') + 1)

export type SkillEffect = { check: DevCheck | undefined; isDirtying: boolean }

export const skillEffect = (skill: string): SkillEffect => {
  const bare = bareName(skill)
  const check = SKILL_CHECKS.find(name => name === bare)
  return { check, isDirtying: check !== undefined || NEW_WORK_SKILLS.has(bare) }
}

export const withCheck = (checks: DevChecks, check: DevCheck): DevChecks =>
  check === 'code-review' ? { ...checks, [check]: true, [ADDRESSED]: false } : { ...checks, [check]: true }

export const withoutChecks = (checks: DevChecks, cleared: readonly DevCheck[]): DevChecks => {
  const isCleared = (check: DevCheck) => cleared.includes(check) || (check === ADDRESSED && cleared.includes('code-review'))
  return Object.fromEntries(CHECKS.map(check => [check, checks[check] && !isCleared(check)])) as DevChecks
}

export const awaitsAddressing = (checks: DevChecks): boolean => checks['code-review'] && !checks[ADDRESSED]

export const sameChecks = (a: DevChecks, b: DevChecks): boolean => CHECKS.every(check => a[check] === b[check])

export const asChecks = (value: unknown): DevChecks | undefined => {
  if (typeof value !== 'object' || value === null) return undefined
  const fields = value as Record<string, unknown>
  const field = (check: DevCheck) => (check === ADDRESSED ? (fields[check] ?? false) : fields[check])
  return CHECKS.every(check => typeof field(check) === 'boolean')
    ? (Object.fromEntries(CHECKS.map(check => [check, field(check)])) as DevChecks)
    : undefined
}

const isPhaseRecord = (value: unknown): boolean => value === null || (typeof value === 'object' && 'phase' in value)

export const asStoredChecks = (value: unknown): DevChecks | undefined =>
  asChecks(value) ?? (isPhaseRecord(value) ? UNCHECKED : undefined)

export const recordBefore = (
  before: ReadonlyMap<DevCheck, boolean>,
  ran: DevCheck,
  current: DevChecks,
  next: DevChecks,
): Map<DevCheck, boolean> =>
  new Map([
    ...before,
    ...CHECKS.filter(check => (check === ran || current[check] !== next[check]) && !before.has(check)).map(
      check => [check, current[check]] as const,
    ),
  ])

export const restoreChecks = (checks: DevChecks, before: ReadonlyMap<DevCheck, boolean>): DevChecks =>
  Object.fromEntries(CHECKS.map(check => [check, before.get(check) ?? checks[check]])) as DevChecks

const GIT_COMMIT = /\bgit\b(?:\s+-C\s+\S+)?\s+commit\b/

export const isGitCommit = (command: string): boolean => GIT_COMMIT.test(command)

const CHECK_RUN =
  /\b(pytest|jest|vitest|mocha|rspec|unittest|cargo test|go test|flutter test|dart test|swift test|xcodebuild test|eslint|ruff|mypy|pyright|tsc|biome|shellcheck|golangci-lint|swiftlint|dart analyze|flutter analyze)\b|\b(npm|yarn|pnpm|bun|make|just|claude plugin)\b.*\b(test|lint|check|typecheck|analyze|validate)\b/

export const isCheckRun = (command: string): boolean => CHECK_RUN.test(command)

export const isCheckpoint = (command: string): boolean => isGitCommit(command) || isCheckRun(command)

export const IDLE_MS = 30_000
export const MODEL_TIMEOUT_MS = 20_000
export const MAX_TOKENS = 80

const CHECKS_PREFIX = 'session:'

export const checksKey = (sessionId: string): string => `${CHECKS_PREFIX}${sessionId}`

const TOPIC_PREFIX = 'topic:'

export const topicKey = (sessionId: string): string => `${TOPIC_PREFIX}${sessionId}`

const sessionOfKey = (key: string): string | undefined =>
  [CHECKS_PREFIX, TOPIC_PREFIX].filter(prefix => key.startsWith(prefix)).map(prefix => key.slice(prefix.length))[0]

export const staleKeys = (keys: readonly string[], kept: number, currentSessionId: string): string[] => {
  const owned = keys.flatMap(key => {
    const sessionId = sessionOfKey(key)
    return sessionId === undefined ? [] : [{ key, sessionId }]
  })
  const lastPosition = new Map(owned.map(({ sessionId }, index) => [sessionId, index]))
  const dropped = new Set(
    [...lastPosition.entries()]
      .sort((a, b) => b[1] - a[1])
      .slice(kept)
      .map(([sessionId]) => sessionId)
      .filter(sessionId => sessionId !== currentSessionId),
  )
  return owned.filter(({ sessionId }) => dropped.has(sessionId)).map(({ key }) => key)
}

export const asTopic = (value: unknown): DevTopic | undefined => {
  if (typeof value !== 'object' || value === null) return undefined
  const { name, at, titled } = value as Record<string, unknown>
  if (typeof name !== 'string' || typeof at !== 'number') return undefined
  return typeof titled === 'string' ? { name, at, titled } : { name, at }
}

export const retitle = (topic: DevTopic | null | undefined, title: string | undefined): string | undefined => {
  if (topic == null || topic.name === title) return undefined
  return title === undefined || title === '' || title === topic.titled ? topic.name : undefined
}

const nameTopic = (topic: DevTopic | null, name: string | null, at: number): DevTopic | null => {
  if (name === null) return null
  if (topic?.name === name) return topic
  return { ...topic, name, at }
}

export const verdictState = (
  text: string,
  current: DevState,
  at: number,
  held: readonly DevCheck[] = [],
): DevState | undefined => {
  const stale = parseStale(text)
  const feature = parseFeature(text)
  const addressed = parseAddressed(text)
  if (stale === undefined && feature === undefined && addressed === undefined) return undefined
  const kept = stale === undefined ? current.checks : withoutChecks(current.checks, stale.filter(check => !held.includes(check)))
  return {
    checks: addressed === true && kept['code-review'] ? { ...kept, [ADDRESSED]: true } : kept,
    topic: feature === undefined ? current.topic : nameTopic(current.topic, feature, at),
  }
}

const featureGuide = (topic: DevTopic | null): string => {
  const keep =
    topic === null
      ? ''
      : ` It is currently named "${topic.name}". If that still names the same feature or bug as specifically as asked here, repeat it exactly; otherwise give the new name.`
  return `Feature: the feature or bug the session as a whole is working on, as a noun phrase of at most 35 characters, specific enough to tell it apart from other work in the same repository, such as "CSV export with column picker" or "login redirect loop on Safari"; not the current step. Answer none when the session is not developing software.${keep}`
}

const checksGuide = (checks: DevChecks): string => {
  const set = SKILL_CHECKS.filter(check => checks[check])
  return `Checks: each of ${SKILL_CHECKS.join(', ')} is set when the skill of that name runs. Set now: ${set.length === 0 ? 'none' : set.join(', ')}.
A set check no longer holds when the session has moved on to a different feature or bug than the one it ran for, or when substantial changes were made after its most recent run: changes to behaviour, control flow, state, data handling, interfaces or integrations that could invalidate what it verified. Formatting, comments, renames, documentation, and fixes for problems that check's own run found do not count. When unsure, the check holds.${awaitsAddressing(checks) ? ADDRESSED_GUIDE : ''}`
}

const ADDRESSED_GUIDE = `
Addressed: whether every finding of the most recent code-review run has been dealt with: fixed, or rejected or deferred with a stated reason. A review that reported no findings counts as addressed. Findings still open, partly fixed, or waiting on the user's decision are not addressed. When unsure, answer no.`

const answerFormat = (checks: DevChecks): string =>
  awaitsAddressing(checks)
    ? `Answer with exactly three lines and nothing else:
FEATURE: <name|none>
STALE: <comma-separated set checks that no longer hold|none>
ADDRESSED: <yes|no>`
    : `Answer with exactly two lines and nothing else:
FEATURE: <name|none>
STALE: <comma-separated set checks that no longer hold|none>`

export const forkPrompt = (
  state: DevState,
  answer: string,
): string => `[dev-phase] A status display is asking a side question. Do not continue the work and do not call tools; just answer.

Which feature or bug is this session working on, and do its review checks still hold?

${featureGuide(state.topic)}

${checksGuide(state.checks)}

Your final reply this turn ended with: """${answer.slice(-1200) || '(no text)'}"""

${answerFormat(state.checks)}`

const oneLine = (text: string, max: number): string => text.replace(/\s+/g, ' ').trim().slice(0, max)

const SECRET_PREFIX = /\b(sk-|ghp_|gho_|ghs_|github_pat_|xox[abpr]-|AKIA)[\w-]+/g
const SECRET_FIELD = /\b((?:[\w-]*(?:token|key|secret|password|passwd)|bearer)["']?(?:\s*[=:]\s*|\s+)["']?)[^\s"']+/gi

export const redact = (command: string): string =>
  command.replace(SECRET_PREFIX, '$1***').replace(SECRET_FIELD, '$1***')

const EDIT_TOOLS = new Set(['Edit', 'MultiEdit', 'Write', 'NotebookEdit'])

const PATH_MAX = 80

const HOME_DIR = /^\/(?:Users|home)\/[^/]+(?=\/|$)/

const shortPath = (path: string): string => {
  const short = oneLine(path.replace(HOME_DIR, '~'), Infinity)
  return short.length > PATH_MAX ? `…${short.slice(1 - PATH_MAX)}` : short
}

const editedPath = (input: Readonly<Record<string, unknown>>): string | undefined =>
  [input.file_path, input.notebook_path, input.path].find((path): path is string => typeof path === 'string')

const describeUse = (use: DigestToolUse): string => {
  const { skill, command } = use.input
  if (use.tool === 'Skill' && typeof skill === 'string') return `Skill(${skill})`
  if (use.tool === 'Bash' && typeof command === 'string') return `Bash(${oneLine(redact(command), 60)})`
  const path = EDIT_TOOLS.has(use.tool) ? editedPath(use.input) : undefined
  return path === undefined ? use.tool : `${use.tool}(${shortPath(path)})`
}

const TOOLS_PER_ROW = 12

const describeUses = (uses: readonly DigestToolUse[]): string => {
  if (uses.length === 0) return ''
  const shown = uses.slice(-TOOLS_PER_ROW).map(describeUse)
  const skipped = uses.length - shown.length
  return ` [${skipped > 0 ? `+${skipped} more, ` : ''}${shown.join(', ')}]`
}

export const digest = (messages: readonly DigestMessage[], rows = 40): string => {
  const kept = messages.filter(message => message.text.trim() !== '' || message.toolUses.length > 0).slice(-rows)
  return kept
    .map((message, index) => {
      const text = oneLine(message.text, index === kept.length - 1 ? 1500 : 300)
      return `${message.role}: ${text}${describeUses(message.toolUses)}`
    })
    .join('\n')
}

export const digestPrompt = (
  state: DevState,
  rows: string,
): string => `You track a software development session: which feature or bug it is working on, and whether its review checks still hold. Below are the last messages of its transcript, oldest first; tool calls are in square brackets.

${featureGuide(state.topic)}

${checksGuide(state.checks)} A set check whose most recent run is not in the transcript below ran before all of it, so every change shown came after that run.

<transcript>
${rows}
</transcript>

${answerFormat(state.checks)}`

const answerLine = (text: string, label: string): string | undefined =>
  [...text.matchAll(new RegExp(`^[\\s>*_#-]*${label}[*_]*:[*_]*[ \\t]*(.*)$`, 'gim'))].at(-1)?.[1]

const normalise = (name: string): string =>
  name
    .replace(/\([^)]*\)/g, '')
    .replace(/[*`"'[\]]/g, '')
    .trim()
    .toLowerCase()
    .replace(/[.!]+$/, '')
    .replace(/[\s_]+/g, '-')

const staleNames = (text: string): string[] | undefined =>
  answerLine(text, 'STALE')
    ?.split(/,|;|\band\b/)
    .map(normalise)
    .filter(name => name !== '')

const isAll = (name: string): boolean => name === 'all' || name.startsWith('all-')

export const parseStale = (text: string): DevCheck[] | undefined => {
  const names = staleNames(text)
  if (names === undefined) return undefined
  return names.some(isAll) ? [...SKILL_CHECKS] : SKILL_CHECKS.filter(check => names.includes(check))
}

export const unknownStale = (text: string): string[] =>
  (staleNames(text) ?? []).filter(name => name !== 'none' && !isAll(name) && !SKILL_CHECKS.some(check => check === name))

export const parseAddressed = (text: string): boolean | undefined => {
  const answer = /^(yes|no)\b/.exec(normalise(answerLine(text, 'ADDRESSED') ?? ''))?.[1]
  return answer === undefined ? undefined : answer === 'yes'
}

export const parseFeature = (text: string): string | null | undefined => {
  const named = answerLine(text, 'FEATURE')
    ?.trim()
    .replace(/^["'`*]+|["'`.*]+$/g, '')
    .trim()
  if (named === undefined || named === '') return undefined
  return named.toLowerCase() === 'none' ? null : named.slice(0, 40)
}
