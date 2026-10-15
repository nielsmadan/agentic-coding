export type DevPhase =
  | 'planning'
  | 'implementation'
  | 'agent QA'
  | 'QA fixes'
  | 'code review'
  | 'review fixes'
  | 'manual QA'
  | 'wrap-up'

export type DevPhaseSource = 'skill' | 'edit' | 'fork' | 'log'

export type DevPhaseRecord = { phase: DevPhase; at: number; source: DevPhaseSource }

export type DevTopic = { name: string; at: number; titled?: string }

declare module 'claude-code' {
  interface PluginState {
    'dev-phase': { current: DevPhaseRecord | null; topic: DevTopic | null }
  }
}
