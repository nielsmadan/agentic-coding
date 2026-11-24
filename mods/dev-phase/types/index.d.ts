export type DevCheck = 'code-review' | 'fixes-made' | 'qa' | 'qa-tour'

export type DevChecks = Readonly<Record<DevCheck, boolean>>

export type DevTopic = { name: string; at: number; titled?: string }

export type DevNote = { checks: readonly DevCheck[]; reason: string; at: number }

export type DevState = { checks: DevChecks; topic: DevTopic | null; note?: DevNote | null }

declare module 'claude-code' {
  interface PluginState {
    'dev-phase': DevState
  }
}
