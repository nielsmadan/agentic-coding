## Sandbox

Every agent CLI runs inside a [nono](https://github.com/nolabs-ai/nono) Seatbelt sandbox.
`~/wrksp` is read+write; most of the rest of `$HOME` is not.

**A denial footer is not a failure.** nono prints `Sandbox denial: N paths blocked` at exit
even on successful runs, listing harmless probes (tools walking up from the workdir looking
for config). Check the command's **exit code and output** before concluding the sandbox blocked
anything. Do not rewrite a command, call a binary by its full path, or skip a verification step
on the strength of that footer.

**`Operation not permitted` has two very different causes**, and they need opposite responses:

1. *A missing grant.* Confirm with **`nono why --self --path <path> --op <read|write|readwrite>`**.
   If it reports `path_not_granted` or `filesystem_deny`, say so and stop — the profile needs a
   new grant, which is the user's call. Never work around it by relocating files or weakening a
   test.

   **`--self` is not optional.** Without it, `nono why` evaluates nono's *default* profile
   rather than the running session, and reports `DENIED / path_not_granted` for almost any path
   — even when run outside a sandbox entirely, and even for paths the session can freely write.
   A bare `nono why` is never evidence that something is blocked, nor that you are sandboxed.
   `nono why --self` prints `NOT SANDBOXED` when you are not.

   **`nono why` also ignores `bypass_protection`.** A path in a permanent deny group that a
   profile re-opens with `bypass_protection` still reports `DENIED / filesystem_deny`, while the
   sandboxed process reads it fine. If `nono why` says denied but the command works, believe the
   command.
2. *A tool sandboxing itself.* Seatbelt cannot nest, so any tool that calls `sandbox-exec`
   fails inside nono. The giveaway is `sandbox-exec: sandbox_apply: Operation not permitted`,
   or an error naming a path that `nono why` says is **allowed**. The fix is to disable the
   inner sandbox, never to grant a path:

   | tool | flag |
   |---|---|
   | `swift build` / `swift test` / `swift run` | `--disable-sandbox` |
   | `xcodebuild` | `-IDEPackageSupportDisableManifestSandbox=1 -IDEPackageSupportDisablePluginExecutionSandbox=1` (the swiftc flag is already in the environment) |
   | Chrome / Chromium | `--no-sandbox` |

**Known limits, not bugs.** Xcode test targets with a host application (`TEST_HOST` set) cannot
run sandboxed: the app is launched through LaunchServices, lands outside the sandbox, and its
connection back in never establishes. Report it and let the user run those in an unsandboxed
session. `swift test` on a `Package.swift` target has no such problem.
