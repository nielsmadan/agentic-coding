import { appendFile } from 'node:fs/promises'
import { homedir } from 'node:os'
import { join } from 'node:path'

import { truncateToWidth } from '@earendil-works/pi-tui'

import { createDevPhase } from './extension'

const LOG = join(process.env.PI_CODING_AGENT_DIR ?? join(homedir(), '.pi', 'agent'), 'dev-phase.log')

const debug = (text: string): void => {
  if (process.env.PI_DEV_PHASE_DEBUG !== '1') return
  void appendFile(LOG, `${new Date().toISOString()}  dev-phase: ${text}\n`).catch(() => undefined)
}

export default createDevPhase({
  setTimer: (run, ms) => setTimeout(run, ms),
  clearTimer: handle => clearTimeout(handle as ReturnType<typeof setTimeout>),
  now: () => Date.now(),
  abortController: () => new AbortController(),
  deadline: (signal, ms) => AbortSignal.any([signal as AbortSignal, AbortSignal.timeout(ms)]),
  truncate: (text, width) => truncateToWidth(text, width),
  home: homedir(),
  debug,
})
