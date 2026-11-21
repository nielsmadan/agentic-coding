---
name: configure-agents
description: Set up a new agent CLI (harness) on this machine with the house configuration — a nono sandbox profile, a sops-injecting shell wrapper, loadout wiring, model-reviewed permission checks, the shared status line, the sandbox-status and Juggler hooks, and the repo's per-harness integrations — or audit an existing harness against those settings and fix the gaps. Use when the user says "configure agents", "add agent X", "onboard a new agent CLI", "set up X like the other agents", "configure X like claude/codex", "sandbox X", "give X our usual settings", or "is X configured like the others". Not for picking models (use agent-models) or changing one setting the user named.
argument-hint: "agent-name [--audit]"
---

# Configure Agents

Bring one harness to the configuration every other agent here runs with. The
house values and the per-harness precedents are in
[`references/house-settings.md`](references/house-settings.md); read it first.

Two modes:

- **New harness** (default): walk every step below.
- **`--audit`**, or the harness already has `nono/<agent>-local.json`: compare
  each step against what exists, list the gaps as a table (concern, house value,
  current, fix), and implement only the gaps the user approves.

## Instructions

### Step 1: Learn the harness

Before writing anything, establish from its docs and binary:

- config file path and format; project-level config, if any
- permission modes, and whether one is model-reviewed
- status line support (command, built-in items, or none)
- hook events, and how a `SessionStart` hook passes context to the model
- where it keeps install, state, credentials and logs; whether login uses the keychain
- its own sandbox flag; whether it imports other harnesses' skills or config
- whether loadout supports it: `docs/user/reference/harnesses.md` in the loadout repo

Save the fetched pages to the scratchpad and quote them when stating a fact.
Where the docs are silent, probe the binary (`<agent> --help`, `strings`) and say
the result is observed, not documented.

### Step 2: nono profile

1. If a vendor pack exists, `nono pull nolabs-ai/<agent>` and extend it, as
   `claude-local` does. Otherwise write `nono/<agent>-local.json` from scratch,
   modelled on `nono/devin-local.json`: extend `default`, `agent-common`,
   `agent-private`, grant the install tree read-only, and grant each state path
   one by one (`allow` for directories, `allow_file` for files).
2. Never grant the login keychain or `~/.ssh`. A keychain login becomes an API
   key from the sops store, plus a memory-only credential store if the CLI has one.
3. Add the symlink to `sync.sh`'s `SYMLINKS` and run `./sync.sh`.
4. Run `bin/nono-audit`, review what the new profile can write, then
   `bin/nono-audit --update` and read the baseline diff.
5. Add a paragraph to `docs/nono-grants.md` covering what is granted, what stays
   denied and why.

Success: `nono why --profile <agent>-local --path ~/Library/Keychains/login.keychain-db --op read`
denies, and the agent starts and logs in under the profile.

### Step 3: Shell wrapper

Write `.airc.d/<agent>.zsh` with `<agent>() { _agent_sandboxed <agent>-local <agent> "$@"; }`.
Wrap every name the installer links (Cursor has both `cursor-agent` and `agent`).
Set `AGENT_HARNESS=<agent>` when a shared script must tell harnesses apart. Add the
profile to the `--silent` list in `.airc.d/05-sandbox.zsh` if the CLI draws a
fullscreen TUI or probes denied paths on every start. Add the agent to
`bin/update-agents` and its test. Then `source ~/.airc`.

### Step 4: Loadout wiring and settings

1. Add `[<agent>]` to `loadout.toml` with `settings = "<agent>"`.
2. Write `loadout/settings/<agent>.json` with the house values from the reference:
   the default model, the permission mode (Step 5), history retention, no
   attribution, quiet UI, no startup update check, subagent limits, its own
   sandbox off, and imports of other harnesses' config off.
3. Ask the user whether the Studio profiles (`studio.toml`, `studio-agents.toml`)
   should get the harness; don't add it by default.
4. Run `loadout check --global` first and read the diff. A key the harness writes
   for itself (Devin's `theme_mode`) is carried over and never rendered, so leave
   it out of the slice. A key loadout manages as a whole (Devin's `hooks`) replaces
   whatever else wrote there; see Step 7 before syncing.
5. Run `loadout sync --global`. A non-zero exit can come from unrelated project
   targets, so read every `ERROR` line before blaming the change.
6. Start one session and check which instruction and rule files it loaded. A
   harness that imports other harnesses' config can load the global instructions
   twice (Devin loaded Cursor's `loadout.mdc` beside its own `AGENTS.md`).

### Step 5: Permission checks

Pick the harness's model-reviewed mode (Claude `auto`, Codex `auto_review`,
Devin `smart`). If it has none, propose bypass inside nono and say so. Ask the
user before choosing anything with fewer checks than the reviewed mode.

A user's explicit choice of mode stands; record it in the reference table.

Verify it with a non-interactive probe in a scratch git repo under `~/wrksp`, on
the cheapest model, covering a plain command, a `&&` chain, a heredoc written
outside the workspace, and `git push`. Expect the first three to run and the push
to be denied by loadout's rule. Check the files on disk, not the agent's reply.

Run the probe through the wrapper, with the deadline outside the shell:
`timeout 200 zsh -c 'source ~/.airc; <agent> -p …'`. Writing `timeout <agent>`
inside the shell runs the binary directly and skips the sandbox. Each probe
leaves a session in the harness's history; delete them afterwards.

### Step 6: Status line

Reproduce the shared layout described in the reference: sandbox lock, model and
effort, context bar, then quota. Choose by what the harness offers:

- A command status line: a script under `loadout/module-config/<agent>/`, ported
  from `loadout/module-config/claude/hooks/statusline.sh` or the Droid Python one.
  Give it a test if it parses anything.
- Built-in items only: the closest equivalents, in the same order (as Codex does).
- None: tell the user it isn't possible and move on.

### Step 7: Hooks

- **Sandbox status:** add `loadout/hooks/<agent>.json` with a `SessionStart` hook
  running `~/.local/bin/agent-sandbox-status`, and list it under `hooks` in
  `loadout.toml`. If the harness wants JSON rather than stdout, add a branch keyed
  on `AGENT_HARNESS` to `bin/agent-sandbox-status` with a test, as Cursor has.
  If the harness has no such hook, say so.
- **Juggler:** add `loadout/juggler/hooks/hooklinesinker-<agent>.json` if
  hooklinesinker supports the agent, using `~/`-relative commands with the events
  and timeout it installs itself. hooklinesinker treats those as installed and
  leaves them alone. This is required whenever loadout owns the harness's whole
  hooks block, since the sync otherwise deletes the entries Juggler wrote. Then
  run `python3 bin/juggler-studio` to regenerate the Studio copy, and confirm
  with `~/.local/share/hooklinesinker/bin/hooklinesinker hooks status --agent <agent>`.
  Don't edit the Juggler or hooklinesinker repos without approval.
- **Check that the note arrives:** ask a probe session (through the wrapper) to
  quote its sandbox status note. It must say INSIDE and name `<agent>-local`.

### Step 8: Integrations

Teach the repo's tools about the new harness: session search in
`loadout/skills/check-agent-logs/scripts/search_agent_logs.py`, `skill-usage`,
and `AGENTS` in `bin/term-peek`. Update `AGENTS.md`'s structure and sandbox
sections. List anything you skip, with the reason.

### Step 9: Verify and report

```bash
source ~/.airc
loadout check --global          # clean, apart from known unrelated project errors
bin/nono-audit --check
python3 -m unittest discover -s bin -p 'test_*.py'
```

Run the Step 5 probe through the wrapper this time, so it runs under nono. Then
report one row per concern: what was set, where, and how it was verified. Leave
the commit to the user unless they asked for one.

## Examples

### Example 1: a new harness

User says: "configure-agents devin"

1. The docs give `~/.config/devin/config.json`, `permission_mode` values, no
   status line, and `read_config_from` imports, which default on. Login writes a
   plain credentials file, so it works in nono.
2. Write `nono/devin-local.json` from scratch, with state files listed one by
   one. Add the `sync.sh` symlink, update the audit baseline, and document it in
   `docs/nono-grants.md`.
3. Write `.airc.d/devin.zsh`, add `devin-local` to `--silent`, and add it to
   `update-agents`.
4. Add `[devin]` to `loadout.toml` and write `devin.json` with the default
   model, `permission_mode: "smart"` (unless the user picks another),
   `attribution`, `auto_update` and `show_hints` off, and every
   `read_config_from` import off except `agents_standard`. Sync.
5. Probe: a chain and a heredoc run, and `git push` is denied.
6. No status line exists; tell the user.
7. Its `SessionStart` hook wants `hookSpecificOutput.additionalContext` JSON, so
   add a `devin` branch to `bin/agent-sandbox-status` and set
   `AGENT_HARNESS=devin` in the wrapper. Loadout owns Devin's whole `hooks` block,
   so render Juggler's Devin hooks through loadout too.

### Example 2: an audit

User says: "is cursor configured like the others?"

Read `nono/cursor-local.json`, `.airc.d/cursor.zsh`, the `[cursor]` table,
`loadout/settings/cursor.json` and `~/.cursor/cli-config.json`. Report the gaps,
for example: `approvalMode` is set by hand rather than through loadout; there is
no status line; no history retention is set. Wait for the user to pick which to
fix.

## Troubleshooting

### The agent reports "Not logged in" under nono
**Cause:** The interactive login lives in the login keychain, which every profile denies on purpose.
**Solution:** Authenticate with an API key from the sops store, injected by `sops-exec` through the wrapper. Ask the user to add the key; never read the store.

### A new state file is denied after an update
**Cause:** `allow_file` grants exact names, so a release that adds a file under the state directory is denied.
**Solution:** Confirm with `nono why --self --path <file> --op write` from inside a session, add the entry, then re-run `bin/nono-audit --update`.

### The agent's own sandbox fails to start
**Cause:** nono already applied a Seatbelt profile, and macOS rejects a nested one.
**Solution:** Turn the harness's sandbox off in its settings slice. nono is the boundary.

### Loadout refuses to write the harness's config
**Cause:** The destination was edited by hand or by another tool after the last sync.
**Solution:** Diff it against the source, move the wanted keys into `loadout/settings/<agent>.json`, and ask the user to run `loadout sync --global --force`.
