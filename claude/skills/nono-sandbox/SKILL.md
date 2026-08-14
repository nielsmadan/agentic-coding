---
name: nono-sandbox
description: Decide whether a failure is actually a nono sandbox denial before treating it as one. Use when a command fails with "Operation not permitted", "sandbox-exec: sandbox_apply", EACCES, EPERM, or a "Sandbox denial" footer. Most such failures on this machine are NOT missing grants — verify first, then either disable a nested sandbox or report a real denial to the user.
---

# Working inside a nono sandbox

`~/wrksp` is read+write. Package caches, agent config and a few named files are granted.
Most of the rest of `$HOME` is not.

**Most failures that look like sandbox denials are not.** Of the sandbox reports raised on this
machine, two thirds turned out to be something else — a tool sandboxing itself, a misread
diagnostic, or an unrelated failure with a plausible-looking error string. Treat "the sandbox
blocked me" as a hypothesis to test, never a conclusion to report.

## Before you conclude anything

**1. Did the command actually fail?** nono prints `Sandbox denial: N paths blocked` at exit
**even on successful runs**, listing harmless probes — tools walking up from the workdir looking
for config. Check the exit code and the real output first. A denial footer next to a failure
does not mean it caused the failure.

**2. Quote the path from the error.** If you cannot point at a line of output naming a specific
path, you do not have a sandbox problem — you have a guess. Never report a denial with a
placeholder path.

**3. Verify that exact path:**

```
nono why --self --path /the/path/from/the/error --op read|write|readwrite
```

`--self` is **not optional**. Without it, `nono why` evaluates nono's *default* profile rather
than the running session and reports `DENIED / path_not_granted` for almost anything — including
from a shell that is not sandboxed at all. A bare `nono why` is never evidence.

Two ways `nono why` still misleads you:

- **It misreports grants inside the built-in keychain protection.** A `read_file` grant on a
  path under `~/Library/Keychains` is honored by the sandbox while `nono why` reports
  `DENIED / filesystem_deny`. If it says denied but the command works, believe the command.
- **It resolves real paths.** A path that does not exist yet reports `path_not_granted` even
  when its parent directory is granted.

When the verdict contradicts the error, trust an actual read or write inside `nono run` over
either.

## The most common cause: a tool sandboxing itself

Seatbelt **cannot nest**. Any tool that calls `sandbox-exec` fails inside nono. The giveaway is
`sandbox-exec: sandbox_apply: Operation not permitted`, or an error naming a path that
`nono why --self` says is **allowed**.

This is *not* a missing grant and no grant will fix it. Disable the inner sandbox:

| tool | flag |
|---|---|
| `swift build` / `swift test` / `swift run` | `--disable-sandbox` |
| `xcodebuild` | `-IDEPackageSupportDisableManifestSandbox=1 -IDEPackageSupportDisablePluginExecutionSandbox=1` |
| Chrome / Chromium | `--no-sandbox` |
| Codex | `-c sandbox_mode="danger-full-access"` |

The wrappers already set `OTHER_SWIFT_FLAGS` and `AGENT_BROWSER_ARGS`, so swiftc and
agent-browser are handled; SwiftPM and xcodebuild take theirs from argv only.

## Known limits — report these, do not try to fix them

- **Xcode test targets with a host application** (`TEST_HOST` set) cannot run sandboxed: the app
  launches via LaunchServices, lands outside the sandbox, and its connection back never
  establishes. `swift test` on a `Package.swift` target is unaffected.
- **A profile change does not reach a running session.** Seatbelt applies the policy at process
  start. If a grant was added after this session began, it is invisible until restart — say so
  rather than asking for it again.

## When it is a real denial

Say so plainly, quote the path and the `nono why --self` verdict, and **stop**. Adding a grant is
the user's decision: it widens the boundary for every agent on the machine, and some paths that
look like config hold credentials.

Do **not**:

- offer `nono run --allow …` or `nono profile promote` as remedies — profiles live in
  `~/ac/nono/`, are version-controlled, and are edited there, not drafted ad hoc
- relocate files, weaken a test, or call a binary by another path to get around it
- ask a peer session to read the path for you
