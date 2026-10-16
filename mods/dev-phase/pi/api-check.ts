import type { ExtensionAPI, ExtensionContext, ExtensionEvent } from '@earendil-works/pi-coding-agent'

import type { Pi, PiContext, PiEvents } from './extension'
import devPhase from './index'

type Payload<K extends string> = Extract<ExtensionEvent, { type: K }>

export const entry: (pi: Pi<AbortSignal>) => void = devPhase

export const context = (ctx: ExtensionContext): PiContext<AbortSignal> => ctx

export const api = (pi: ExtensionAPI): Omit<Pi<AbortSignal>, 'on'> => pi

export const events: { [K in keyof PiEvents]: (event: Payload<K>) => PiEvents[K] } = {
  session_start: event => event,
  session_tree: event => event,
  session_shutdown: event => event,
  message_end: event => event,
  agent_start: event => event,
  tool_result: event => event,
  user_bash: event => event,
  turn_end: event => event,
  agent_end: event => event,
  agent_settled: event => event,
}
