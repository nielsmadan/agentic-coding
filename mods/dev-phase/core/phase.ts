import type { DevPhase, DevPhaseRecord, DevPhaseSource, DevTopic } from '../types'

type PhaseInfo = { skills: readonly string[]; guide: string }

export type DigestToolUse = { tool: string; input: Readonly<Record<string, unknown>> }

export type DigestMessage = { role: 'user' | 'assistant'; text: string; toolUses: readonly DigestToolUse[] }

const PHASE_INFO = {
  planning: {
    skills: [
      'plan',
      'superpowers:brainstorming',
      'superpowers:writing-plans',
      'blind-spots',
      'review-plan',
      'longshot',
      'ideation',
    ],
    guide: 'brainstorming, designing, or writing or reviewing a plan; no code written for it yet',
  },
  implementation: {
    skills: [
      'superpowers:executing-plans',
      'superpowers:subagent-driven-development',
      'superpowers:test-driven-development',
    ],
    guide: 'writing or debugging the code for the task',
  },
  'agent QA': {
    skills: ['qa', 'test', 'run', 'perf-test'],
    guide: "the agent verifying its own work: test suites, QA passes, running the app, perf tests",
  },
  'QA fixes': {
    skills: [],
    guide: "fixing problems that QA (the agent's or the user's own testing) found",
  },
  'code review': {
    skills: ['code-review', 'simplify', 'security-review', 'superpowers:requesting-code-review'],
    guide: 'reviewing the finished change (code review, simplify, security review)',
  },
  'review fixes': {
    skills: ['review-todo', 'superpowers:receiving-code-review'],
    guide: 'addressing code review findings',
  },
  'manual QA': {
    skills: [],
    guide: "the agent's work is done and the user needs to try it themselves",
  },
  'wrap-up': {
    skills: ['commit', 'squash-commits', 'doc', 'superpowers:finishing-a-development-branch'],
    guide: 'squashing, committing, updating docs, finishing the branch',
  },
} as const satisfies Record<DevPhase, PhaseInfo>

const PHASES = Object.keys(PHASE_INFO) as readonly DevPhase[]

const SOURCES = ['skill', 'edit', 'fork', 'log'] as const satisfies readonly DevPhaseSource[]

const FIX_SKILLS = new Set(['hard-fix', 'superpowers:systematic-debugging', 'pre-existing'])

const NOT_CODE_REVIEW = new Set(['review-logs', 'review-product', 'review-history'])

const SKILL_PHASE = new Map<string, DevPhase>(
  PHASES.flatMap(phase => PHASE_INFO[phase].skills.map(skill => [skill, phase] as const)),
)

export const bareName = (skill: string): string => skill.slice(skill.lastIndexOf(':') + 1)

const fixPhase = (current: DevPhase | undefined): DevPhase => {
  switch (current) {
    case 'agent QA':
    case 'manual QA':
    case 'QA fixes':
      return 'QA fixes'
    case 'code review':
    case 'review fixes':
      return 'review fixes'
    case undefined:
    case 'planning':
    case 'implementation':
    case 'wrap-up':
      return 'implementation'
  }
}

export const phaseOfSkill = (skill: string, current: DevPhase | undefined): DevPhase | undefined => {
  const bare = bareName(skill)
  if (FIX_SKILLS.has(skill) || FIX_SKILLS.has(bare) || FIX_SKILLS.has(`superpowers:${bare}`)) {
    return fixPhase(current)
  }
  return (
    SKILL_PHASE.get(skill) ??
    SKILL_PHASE.get(`superpowers:${bare}`) ??
    SKILL_PHASE.get(bare) ??
    (bare.startsWith('review-') && !NOT_CODE_REVIEW.has(bare) ? 'code review' : undefined)
  )
}

const DOC_FILE = /\.(md|mdx|txt|rst)$/i

export const provisionalPhase = (current: DevPhase | undefined, path: string): DevPhase | undefined => {
  if (DOC_FILE.test(path)) return undefined
  switch (current) {
    case undefined:
    case 'planning':
      return 'implementation'
    case 'agent QA':
    case 'manual QA':
      return 'QA fixes'
    case 'code review':
      return 'review fixes'
    case 'implementation':
    case 'QA fixes':
    case 'review fixes':
    case 'wrap-up':
      return undefined
  }
}

export const isGitCommit = (command: string): boolean =>
  /\bgit\b(?:\s+-C\s+\S+)?\s+commit\b/.test(command)

const CHECK_RUN =
  /\b(pytest|jest|vitest|mocha|rspec|unittest|cargo test|go test|flutter test|dart test|swift test|xcodebuild test|eslint|ruff|mypy|pyright|tsc|biome|shellcheck|golangci-lint|swiftlint|dart analyze|flutter analyze)\b|\b(npm|yarn|pnpm|bun|make|just|claude plugin)\b.*\b(test|lint|check|typecheck|analyze|validate)\b/

export const isCheckRun = (command: string): boolean => CHECK_RUN.test(command)

export const isCheckpoint = (command: string): boolean => isGitCommit(command) || isCheckRun(command)

export const IDLE_MS = 30_000
export const MODEL_TIMEOUT_MS = 20_000
export const MAX_TOKENS = 60

export const NO_PHASE_LABEL = '● no phase yet'

export const isProvisional = (record: DevPhaseRecord): boolean => record.source === 'edit'

export const featureSuffix = (topic: DevTopic | null): string => (topic === null ? '' : ` · ${topic.name}`)

const STORE_PREFIX = 'session:'

export const storeKey = (sessionId: string): string => `${STORE_PREFIX}${sessionId}`

const TOPIC_PREFIX = 'topic:'

export const topicKey = (sessionId: string): string => `${TOPIC_PREFIX}${sessionId}`

const sessionOfKey = (key: string): string | undefined =>
  [STORE_PREFIX, TOPIC_PREFIX].filter(prefix => key.startsWith(prefix)).map(prefix => key.slice(prefix.length))[0]

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

const isPhase = (value: unknown): value is DevPhase => PHASES.some(phase => phase === value)

const isSource = (value: unknown): value is DevPhaseSource => SOURCES.some(source => source === value)

export const asRecord = (value: unknown): DevPhaseRecord | undefined => {
  if (typeof value !== 'object' || value === null) return undefined
  const { phase, at, source } = value as Record<string, unknown>
  return isPhase(phase) && typeof at === 'number' && isSource(source) ? { phase, at, source } : undefined
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

export const nameTopic = (topic: DevTopic | null, name: string | null, at: number): DevTopic | null => {
  if (name === null) return null
  if (topic?.name === name) return topic
  return { ...topic, name, at }
}

export type DevPhaseState = { record: DevPhaseRecord | null; topic: DevTopic | null }

export const verdictState = (
  text: string,
  current: DevPhaseState,
  at: number,
  source: DevPhaseSource,
): DevPhaseState | undefined => {
  const verdict = parseVerdict(text)
  if (verdict === undefined) return undefined
  const feature = parseFeature(text)
  return {
    topic: feature === undefined ? current.topic : nameTopic(current.topic, feature, at),
    record: verdict === null ? null : { phase: verdict, at, source },
  }
}

const PHASE_GUIDE = `Phases:
${PHASES.map(phase => `- ${phase}: ${PHASE_INFO[phase].guide}`).join('\n')}
- none: this session is not developing software`

const featureGuide = (topic: DevTopic | null): string => {
  const keep =
    topic === null
      ? ''
      : ` It is currently named "${topic.name}". If that still names the same feature or bug as specifically as asked here, repeat it exactly; otherwise give the new name.`
  return `Feature: the feature or bug the session as a whole is working on, as a noun phrase of at most 35 characters, specific enough to tell it apart from other work in the same repository, such as "CSV export with column picker" or "login redirect loop on Safari"; not the current step.${keep}`
}

const ANSWER_FORMAT = `Answer with exactly two lines and nothing else:
PHASE: <${PHASES.join('|')}|none>
FEATURE: <name|none>`

export const forkPrompt = (
  previous: DevPhaseRecord | null,
  topic: DevTopic | null,
  answer: string,
): string => `[dev-phase] A status display is asking a side question. Do not continue the work and do not call tools; just answer.

Which phase of the user's development process is this session in right now, and which feature or bug is it working on?

${PHASE_GUIDE}

${featureGuide(topic)}

Last recorded phase: ${previous?.phase ?? 'none yet'}
Your final reply this turn ended with: """${answer.slice(-1200) || '(no text)'}"""

${ANSWER_FORMAT}`

const oneLine = (text: string, max: number): string => text.replace(/\s+/g, ' ').trim().slice(0, max)

const SECRET_PREFIX = /\b(sk-|ghp_|gho_|ghs_|github_pat_|xox[abpr]-|AKIA)[\w-]+/g
const SECRET_FIELD = /\b((?:[\w-]*(?:token|key|secret|password|passwd)|bearer)["']?(?:\s*[=:]\s*|\s+)["']?)[^\s"']+/gi

export const redact = (command: string): string =>
  command.replace(SECRET_PREFIX, '$1***').replace(SECRET_FIELD, '$1***')

const describeUse = (use: DigestToolUse): string => {
  const { skill, command } = use.input
  if (use.tool === 'Skill' && typeof skill === 'string') return `Skill(${skill})`
  if (use.tool === 'Bash' && typeof command === 'string') return `Bash(${oneLine(redact(command), 60)})`
  return use.tool
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
  rows: string,
  topic: DevTopic | null,
): string => `You label where a software development session stands and what it is working on. Below are the last messages of its transcript, oldest first; tool calls are in square brackets.

${PHASE_GUIDE}

${featureGuide(topic)}

<transcript>
${rows}
</transcript>

${ANSWER_FORMAT}`

const normalise = (text: string): string => text.toLowerCase().replace(/[\s_-]+/g, '')

export const parseVerdict = (text: string): DevPhase | null | undefined => {
  const named = /PHASE:\s*([a-z _-]+)/i.exec(text)?.[1]
  if (named === undefined) return undefined
  const key = normalise(named)
  if (key === 'none') return null
  return PHASES.find(phase => normalise(phase) === key)
}

export const parseFeature = (text: string): string | null | undefined => {
  const named = /FEATURE:[ \t]*(.*)/i.exec(text)?.[1]?.trim().replace(/^["'`]+|["'`.]+$/g, '').trim()
  if (named === undefined || named === '') return undefined
  return named.toLowerCase() === 'none' ? null : named.slice(0, 40)
}
