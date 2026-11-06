export type DevCheck = 'code-review' | 'findings-addressed' | 'qa' | 'qa-tour'

export type DevChecks = Readonly<Record<DevCheck, boolean>>

export type DevTopic = { name: string; at: number; titled?: string }

export type DevState = { checks: DevChecks; topic: DevTopic | null }

declare module 'claude-code' {
  interface PluginState {
    'dev-phase': DevState
  }
}
