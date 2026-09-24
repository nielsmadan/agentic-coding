## Sandbox

Every agent CLI runs inside a [nono](https://github.com/nolabs-ai/nono) Seatbelt sandbox.
`~/wrksp` is read+write; most of the rest of `$HOME` is not.

**nono's exit diagnostic prints only when the command exits non-zero**, and is not proof of
anything on its own. `Sandbox denial: N path(s) blocked.` lists each path and a `Fix flags:`
line, but those are often harmless probes (tools walking up from the workdir looking for config)
that merely co-occur with an unrelated failure — check the command's **exit code and output**
before concluding the sandbox blocked anything. `No path denials were observed during this
session.` is the opposite signal: nothing was blocked, so look elsewhere. Do not rewrite a
command, call a binary by its full path, or skip a verification step on the strength of a denial
line.

**Claude and OpenCode run nono with `--silent`, so none of that prints.** The failing command's
own `Operation not permitted` still reaches you; nono's banner and exit diagnostic do not, and
their absence is not evidence that nothing was denied. Codex and Pi show both.

**`Operation not permitted` has two very different causes**, and they need opposite responses:

1. *A missing grant.* Confirm with **`nono why --self --path <path> --op <read|write|readwrite>`**.
   If it reports `path_not_granted` or `filesystem_deny`, say so and stop — the profile needs a
   new grant, which is the user's call. Never work around it by relocating files or weakening a
   test.

   **Never offer a grant as the first remedy.** Most of these are not missing grants at all, and
   proposing `nono run --allow` before verifying is what produces repeated false denial reports.
   Verify first, then report; the grant is the user's decision, not the opening move.

   **A profile change never reaches a running session** — Seatbelt applies policy at process
   start. If a grant was added after this session began, say it needs a restart rather than
   asking for it again.

   **`--self` is not optional.** Without it, `nono why` evaluates nono's *default* profile
   rather than the running session, and reports `DENIED / path_not_granted` for almost any path
   — even when run outside a sandbox entirely, and even for paths the session can freely write.
   A bare `nono why` is never evidence that something is blocked, nor that you are sandboxed.
   `nono why --self` prints `NOT SANDBOXED` when you are not.

   **`nono why` can also disagree with the sandbox outright.** A `read_file` grant on a path
   under `~/Library/Keychains` is honored at runtime while `nono why` still reports
   `DENIED / filesystem_deny`. If `nono why` says denied but the command works, believe the
   command.

   **A denied directory says nothing about the files granted inside it.** `~/.android` reports
   `path_not_granted` while `adbkey`, `adbkey.pub` and `adb_known_hosts.pb` inside it are granted,
   and `ls` or a glob over the directory fails either way. Ask about the exact file the failing
   command opens, not its parent.
2. *Something under nono starting its own sandbox.* Nono blocks sandbox re-initialization for
   anything running under the profile — usually a process the agent spawned, not the agent
   itself. The giveaway is `sandbox-exec: sandbox_apply: Operation not permitted`,
   `forbidden-sandbox-reinit` in nono's exit diagnostic (Codex and Pi only), or an error naming
   a path that `nono why` says is **allowed**. The denial carries no path, so no grant can
   address it — disable the inner sandbox instead:

   | tool | flag |
   |---|---|
   | `swift build` / `swift test` / `swift run` | `--disable-sandbox` |
   | `xcodebuild` | `-IDEPackageSupportDisableManifestSandbox=1 -IDEPackageSupportDisablePluginExecutionSandbox=1` (the swiftc flag is already in the environment) |
   | Chrome / Chromium | `--no-sandbox` |

**Known limits, not bugs.** Xcode test targets with a host application (`TEST_HOST` set) cannot
run sandboxed: the app is launched through LaunchServices, lands outside the sandbox, and its
connection back in never establishes. Report it and let the user run those in an unsandboxed
session. `swift test` on a `Package.swift` target has no such problem.

**Some paths are denied on purpose and stay denied** — `~/Library/Keychains/login.keychain-db`
(credentials; codesign against the granted `agent-signing.keychain-db` instead), `~/.ssh`, and
`~/.local/state/mise/trusted-configs` among them. Each blocks
something the user's *own* unsandboxed tools would later trust. Do not propose a grant for these:
name the blocker, hand the user the command to run themselves, and carry on with the rest.
Tell them to run it in their own terminal: a `!` command typed into this session runs inside the
same sandbox and hits the same denial. The
`nono-sandbox` skill lists each one with its command; the reasoning is in `~/ac/docs/security-model.md`.

**`uvx` needs its directories redirected, not granted.** uv writes to
`~/.local/share/uv/tools`, which is not granted, so `uvx <tool>` fails with `Operation not
permitted` on a `.lock` file there. Do not ask for a grant: that directory holds executables the
user's *own* unsandboxed `uv` would later run, the same reason install trees elsewhere are
read-only. Point uv at a writable directory in the workspace instead — measured working:

```sh
env UV_TOOL_DIR="$WORKDIR/.uv/tools" UV_CACHE_DIR="$WORKDIR/.uv/cache" uvx --from <pkg> <cmd>
```
