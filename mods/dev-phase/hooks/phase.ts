import type { SessionMessage, ThemeKey, ToolUseSummary } from 'claude-code'

import type { DevPhase, DevPhaseRecord, DevPhaseSource, DevTopic } from '../types'

type PhaseInfo = { color: ThemeKey; skills: readonly string[]; guide: string }

const PHASE_INFO = {
  planning: {
    color: 'planMode',
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
    color: 'claude',
    skills: [
      'superpowers:executing-plans',
      'superpowers:subagent-driven-development',
      'superpowers:test-driven-development',
    ],
    guide: 'writing or debugging the code for the task',
  },
  'agent QA': {
    color: 'warning',
    skills: ['qa', 'test', 'run', 'perf-test'],
    guide: "the agent verifying its own work: test suites, QA passes, running the app, perf tests",
  },
  'QA fixes': {
    color: 'warning',
    skills: [],
    guide: "fixing problems that QA (the agent's or the user's own testing) found",
  },
  'code review': {
    color: 'suggestion',
    skills: ['code-review', 'simplify', 'security-review', 'superpowers:requesting-code-review'],
    guide: 'reviewing the finished change (code review, simplify, security review)',
  },
  'review fixes': {
    color: 'suggestion',
    skills: ['review-todo', 'superpowers:receiving-code-review'],
    guide: 'addressing code review findings',
  },
  'manual QA': {
    color: 'permission',
    skills: [],
    guide: "the agent's work is done and the user needs to try it themselves",
  },
  'wrap-up': {
    color: 'success',
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

export const phaseColor = (phase: DevPhase): ThemeKey => PHASE_INFO[phase].color

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

const describeUse = (use: ToolUseSummary): string => {
  const { skill, command } = use.input
  if (use.tool === 'Skill' && typeof skill === 'string') return `Skill(${skill})`
  if (use.tool === 'Bash' && typeof command === 'string') return `Bash(${oneLine(command, 60)})`
  return use.tool
}

export const digest = (messages: readonly SessionMessage[], rows = 40): string => {
  const kept = messages.filter(message => message.text.trim() !== '' || message.toolUses.length > 0).slice(-rows)
  return kept
    .map((message, index) => {
      const tools = message.toolUses.length > 0 ? ` [${message.toolUses.map(describeUse).join(', ')}]` : ''
      return `${message.role}: ${oneLine(message.text, index === kept.length - 1 ? 1500 : 300)}${tools}`
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
