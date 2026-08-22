---
name: nono-sandbox
description: Decide whether a failure is actually a nono sandbox denial before treating it as one. Use when a command fails with "Operation not permitted", "sandbox-exec: sandbox_apply", EACCES, EPERM, or a "Sandbox denial" footer. Most such failures on this machine are NOT missing grants — verify first, then either disable a nested sandbox or report a real denial to the user.
opencode:
  description: Diagnose and resolve permission denials when opencode runs inside a nono security sandbox. Use this when a tool call, shell command, or file operation fails with "Operation not permitted", "Permission denied", EACCES, EPERM, landlock, or sandbox-denied errors, or when an outbound network request fails because the host is not on the sandbox allowlist (connection refused, timeout, or proxy/TLS errors).
  version: 1.2.0
  platforms: [macos, linux]
---

::: claude codex pi
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

**4. A denial can arrive as a non-permission errno.** A hidden path reports *absent* to `stat`
and *present* to an operation on it:

```
DENIED   exists(): False   mkdir: EEXIST   open(…,'x'): EEXIST   link: EPERM
GRANTED  exists(): True    mkdir: EEXIST   open(…,'x'): EEXIST   link: CREATED
```

`EEXIST` alone means nothing — it fires on every path that exists. The **disagreement** is the
signal. Calls that check permission before existence stay honest, so this only shows up where
the existence check runs first.

The general form: **the most legible output can point away from the actual cause.** An errno
lying about existence, and a `forbidden-sandbox-reinit` denial suggesting `--allow <path>` when
it carries no path, are the same trap.

## The most common cause: something under nono starting its own sandbox

Nono blocks sandbox re-initialization for **anything** running under the profile — usually not
the agent itself but a process it spawned (SwiftPM evaluating `Package.swift`, xcodebuild's
plugin execution, Chrome's zygote). The giveaway is `sandbox-exec: sandbox_apply: Operation not
permitted`, `forbidden-sandbox-reinit` in the footer, or an error naming a path that
`nono why --self` says is **allowed**.

The denial carries **no path**, so no grant can address it — ignore nono's own
`--allow <path>` suggestion here. Disable the inner sandbox instead:

| tool | flag |
|---|---|
| `swift build` / `swift test` / `swift run` | `--disable-sandbox` |
| `xcodebuild` | `-IDEPackageSupportDisableManifestSandbox=1 -IDEPackageSupportDisablePluginExecutionSandbox=1` |
| Chrome / Chromium | `--no-sandbox` |
| Codex | `-c sandbox_mode="danger-full-access"` |

Most of this is already handled: the wrappers set `OTHER_SWIFT_FLAGS` and
`AGENT_BROWSER_ARGS`, and `bin/sandbox-shims/xcodebuild` appends the two
`-IDEPackageSupport…` flags, which are NSUserDefaults and so reachable only through
argv. A tool that spawns `xcodebuild` itself therefore works without doing anything.
`swift build` and `swift test` still take `--disable-sandbox` on their own command line.

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
:::
::: opencode
**On any EPERM / EACCES / "Operation not permitted" tool or shell failure:** run `nono why --path <blocked-path> --op read` immediately and include its output verbatim in your reply. Do NOT suggest sudo, chmod, or system permission changes. Then offer the user exactly these two options:

- **Option A (quick fix):** `nono run --allow /path/to/needed -- opencode`
- **Option B (persistent fix):** draft a profile to `$XDG_CONFIG_HOME/nono/profile-drafts/<name>.json` extending `opencode`, add the path under `"allow"` or `"read"`, then tell the user to run `nono profile promote <name>` and start sessions with `nono run --profile <name> -- opencode`

# Working inside a nono sandbox

The user has launched you with `nono run --profile <name> -- opencode`. nono enforces filesystem and network limits at the OS level (Landlock on Linux, Seatbelt on macOS). These are kernel-enforced boundaries — retries or workarounds inside opencode cannot grant access that nono hasn't already permitted.

## Identifying a sandbox denial

The denial signature is in the failed tool's output:

- "Operation not permitted"
- "Permission denied"
- "EACCES" / "EPERM"
- "landlock"
- "sandbox: deny"

When you see any of these on a file, shell, or tool failure, it is a nono boundary — not macOS TCC, not Full Disk Access, not Unix file permissions. Do NOT suggest:

- System Settings / Privacy & Security
- `chmod`, `chown`, `sudo`
- "grant Full Disk Access to your terminal"
- Retrying the operation via a different path

Network-egress denials look different: a request to a host that is not on the sandbox allowlist fails as a connection refused, timeout, or TLS/proxy error rather than an EPERM. Those are covered in the Network egress denials section below.

## Diagnosing

Run `nono why` to see exactly why access was denied:

    nono why --path /the/blocked/path --op read

Use `--op write` for write-only failures and `--op readwrite` when the operation needs both.

If `NONO_CAP_FILE` is set, inspect the full capability set:

    cat "$NONO_CAP_FILE"

### Denials that arrive as a non-permission errno

A denied path is hidden from `stat` but still exists, so an operation that checks existence before permission reports it as present. The two answers contradict each other:

    DENIED   exists(): False   mkdir: EEXIST   open(…,'x'): EEXIST   link: EPERM
    GRANTED  exists(): True    mkdir: EEXIST   open(…,'x'): EEXIST   link: CREATED

`EEXIST` on its own means nothing — it fires on every path that exists. The disagreement is the signal. Calls that check permission before existence stay honest, which is why `link` reports EPERM rather than EEXIST.

A tool that stats a directory, finds nothing, tries to create it and dies on "file exists" has hit a denial, not a stale-state bug. `mkdir /path: file exists` from a tool reading its own config directory is the usual shape.

## Two options to present to the user

### Option A — quick fix (one-off)

Exit opencode and restart with the path explicitly allowed:

    nono run --allow /path/to/needed -- opencode

Use `--read` when only read access is needed.

### Option B — persistent fix (draft a profile)

The active profile directory `$XDG_CONFIG_HOME/nono/profiles/` is read-only from inside the sandbox by design. Drafts are written to `$XDG_CONFIG_HOME/nono/profile-drafts/` and the user promotes them out-of-band with `nono profile promote`.

Write the JSON to `$XDG_CONFIG_HOME/nono/profile-drafts/<chosen-name>.json` extending the active profile. Minimal example for read-only access:

    {
      "extends": "opencode",
      "meta": { "name": "<chosen-name>", "version": "1.0.0" },
      "filesystem": { "read": ["/path/to/needed"] }
    }

If the user is on a custom intermediate profile (e.g. `--profile opencode-with-docs` extending `opencode`), change `extends` to that profile's name so the new profile inherits all their customisations.

If a user profile of that name already exists, read `$XDG_CONFIG_HOME/nono/profiles/<chosen-name>.json` first, base your edit on that profile, write the full proposed profile to `$XDG_CONFIG_HOME/nono/profile-drafts/<chosen-name>.json`, and write a SHA-256 of the base bytes to `$XDG_CONFIG_HOME/nono/profile-drafts/<chosen-name>.base`.

Filesystem field choices:
- `"read"` — read-only directory or file access
- `"write"` — write-only access (rare)
- `"allow"` — read+write directory access

For a single file rather than a directory, use `"allow_file"` / `"read_file"` / `"write_file"` instead.

After drafting, tell the user:

    Drafted profile <chosen-name>. Run `nono profile promote <chosen-name>` to review and apply, then start sessions with `nono run --profile <chosen-name> -- opencode`.

## Network egress denials

nono routes outbound traffic through a filtering proxy. When `network.block` is false but a host allowlist is set, only allowlisted hosts are reachable and every other connection fails — usually as a connection refused, timeout, or TLS/proxy error rather than an EPERM. `nono-status` lists the reachable hosts under "reachable hosts". Retries, alternate endpoints, proxies, or DNS changes cannot bypass the proxy; it is OS-enforced.

If a host is genuinely needed, present the same two options as for filesystem denials.

### Option A — quick fix (one-off)

    nono run --allow-domain api.example.com -- opencode

`--allow-domain` is repeatable and accepts a plain hostname for unrestricted access, or a URL with a path glob to restrict to specific endpoints (e.g. `https://github.com/org/**`).

### Option B — persistent fix (draft a profile)

Add the host to `network.allow_domain` in a profile draft extending the active profile:

    {
      "extends": "opencode",
      "meta": { "name": "<chosen-name>", "version": "1.0.0" },
      "network": { "allow_domain": ["api.example.com"] }
    }

Then tell the user to run `nono profile promote <chosen-name>` and start sessions with `nono run --profile <chosen-name> -- opencode`.

## Validating the new profile

`nono profile promote` shows a diff and validates before applying. If the user wants to validate directly:

    nono profile validate --draft <chosen-name>

## Credential injection

The opencode nono profile defines credential routes for common AI providers. nono injects these credentials transparently via its proxy — opencode never sees the raw API key.

Built-in route names: `openai`, `anthropic`, `gemini`, `github`, `gitlab`.

The corresponding keychain accounts (env-var shaped) are:
- `OPENAI_API_KEY` → injected as `Authorization: Bearer …` to `api.openai.com`
- `ANTHROPIC_API_KEY` → injected as `x-api-key: …` to `api.anthropic.com`
- `GOOGLE_API_KEY` → injected as `x-goog-api-key: …` to `generativelanguage.googleapis.com`; opencode sees it as `GEMINI_API_KEY`
- `GITHUB_TOKEN` → injected as `Authorization: token …` to `api.github.com`
- `GITLAB_TOKEN` → injected as `Authorization: Bearer …` to `gitlab.com/api`

Routes are defined in the profile but **disabled by default**. To enable one, create an extending profile and add the route name to `network.credentials`:

    {
      "extends": "opencode",
      "meta": { "name": "opencode-with-anthropic", "version": "1.0.0" },
      "network": { "credentials": ["anthropic"] }
    }

Do not read or write API keys directly from inside the sandbox. Prefer nono phantom credential routes. If opencode stores a key in `$XDG_CONFIG_HOME/opencode/`, it is visible to the sandboxed process — use the proxy route instead.

## Detach and attach

nono supports running opencode in a detached session that survives terminal disconnects:

    nono run --profile opencode --detach -- opencode

nono prints the session ID on start. Reattach from any terminal:

    nono attach <session-id>

The session ID is also available inside the session as `NONO_SESSION_ID`. The installed plugin surfaces it in the `nono-status` command output.

To list active nono sessions:

    nono sessions

To stop a detached session cleanly:

    nono stop <session-id>

Detached sessions inherit the same sandbox profile as interactive ones — the same filesystem grants, credential routes, and network rules apply.

## opencode-specific notes

- opencode state, sessions, config, and cache live under `~/.opencode`, `$XDG_CONFIG_HOME/opencode`, `$XDG_CACHE_HOME/opencode`, `$XDG_DATA_HOME/opencode`, and `$XDG_STATE_HOME/opencode`. The base profile grants all of these read/write.
- The plugin at `$XDG_CONFIG_HOME/opencode/plugins/nono-sandbox.ts` is symlinked from the pack store. It updates automatically on `nono pull`.
- The skill at `$XDG_CONFIG_HOME/opencode/skills/nono-sandbox/` is similarly symlinked.
- The `nono-status` command (registered by the plugin) shows the active capability set, the network egress allowlist (reachable hosts), enabled credential routes, and the session ID for reattach.
- Do not add provider secrets to opencode's own config files. Route them through `network.credentials` in the profile instead.

## Path conventions

Path references in this skill use `$XDG_CONFIG_HOME`. If that variable is not set, substitute `~/.config`. nono and opencode both follow the XDG Base Directory Specification.

## What you should NOT do

- Do not write the profile yourself unless the user explicitly asks for Option B. Present both options first.
- Do not edit the pack-installed profile at `$XDG_CONFIG_HOME/nono/packages/nolabs-ai/opencode/policy.json` — it is overwritten on every `nono pull`.
- Do not retry the failing operation in a different way. The sandbox is OS-enforced; alternative paths, endpoints, or commands hit the same boundary.
- Do not edit registry-managed package files under `$XDG_CONFIG_HOME/nono/packages`; create a profile extension instead.
:::
