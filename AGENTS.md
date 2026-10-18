# AGENTS.md

This file provides guidance to agentic coding tools working in this repository.

## Repository Overview

This repository contains shared configuration for agentic coding tools. It includes skills, hooks, and permission settings that can be used across multiple projects.

## Structure

Everything loadout renders from lives under `loadout/`; the rest of the repo is the shell
environment and the tools around it.

- `loadout.toml` - the manifest: names which slices each harness composes and in what order. Destinations come from loadout's agent preset, so no machine path appears here.
- `loadout/` - every source loadout renders from
  - `permissions.toml` - shell and MCP permission rules for all agents (see Permissions)
  - `mcp.toml` - which MCP servers exist machine-wide (see MCP Servers)
  - `instructions/` - shared prose fragments for each agent's **global** guidance; edit these (see Global Instructions)
  - `skills/` - global skills, rendered to all four harnesses (see Skills)
  - `templates/` - project-type manifests and the shared parts they select (see Project Templates)
  - `settings/` - the hand-maintained half of each harness's settings: `claude.json`, `claude-afk.json`, `droid.json`, `opencode.json`, `pi.json`
  - `hooks/` - hook *wiring* per harness (`claude.json`, `hooklinesinker-claude.json`, `hooklinesinker-codex.json`)
  - `plugins/` - plugin enablement per harness (`claude.json`, `pi.json`, `unsandboxed.json`)
  - `module-config/<harness>/` - files copied to the harness's own config dir; the hook scripts themselves live in `loadout/module-config/claude/hooks/`
  - `defaults/` - `codex.json` (model defaults) and its generated `codex.owned` record
- `nono/` - sandbox profiles, symlinked to `~/.config/nono/profiles/` (see Sandbox)
- `launchd/` - LaunchAgents that `sync.sh` symlinks into `~/Library/LaunchAgents/` and loads
- `codex/strip_nono_block.py` - removes the nono codex pack's block from `~/.codex/config.toml`
- `pratfall/config.toml` - symlinked to `~/.config/pratfall/config.toml`; the `advisor-*` and `cmdgen-*` profiles (see Pratfall). The autonomous and unsandboxed profiles get a rendered copy without `command_prefix` instead, so dispatcher jobs are not wrapped in `sops-exec`; re-run `sync.sh` there after editing it
- `publish/` - renders the public skills collection (see below)
- `mods/` - Claude Code mods (hooks modules); one with a `pi/` folder is also a pi extension. `sync.sh` installs both (see [docs/skills-and-integration.md](docs/skills-and-integration.md))
- `docs/` - deeper reference, notably [`security-model.md`](docs/security-model.md)
- `.airc` - entry point sourced from `~/.zshrc` (symlinked from `~/.airc`); loads everything under `.airc.d/`
- `.airc.d/` - one `.zsh` file per topic, sourced in glob order
  - `00-path.zsh` puts `bin/` on PATH; `10-env.zsh` sets shared env vars; the rest hold aliases/functions per tool
- `bin/` - standalone CLI scripts on PATH (e.g. `ccmove`, `clcof`); add new ones here rather than as zsh functions. `.airc.d/00-path.zsh` covers interactive shells only — a script that must also run under launchd needs an explicit `~/.local/bin` symlink in `sync.sh`'s `SYMLINKS` (as `jina-fetch` and `sops-exec` have)

**Almost nothing is staged in this repo any more.** loadout writes each generated file straight
to the path its agent reads — `~/.claude/settings.json`, `~/.claude/CLAUDE.md`,
`~/.codex/rules/permissions.rules`, `~/.codex/config.toml` and the rest — so a file you are
looking for is usually at its destination, not here. The one generated file that does land in the
repo is `loadout/defaults/codex.owned`. Separately, `nono/*.json` and `pratfall/config.toml` are
hand-maintained sources reached through symlinks, so those are live config you edit in place.

## Shell Config

Add a new alias or shell function: drop it in the appropriate `.airc.d/<topic>.zsh`, or create a new topic file. Reload with `source ~/.airc` (idempotent — re-sourcing does not duplicate PATH entries).

Add a new CLI command with flags, validation, or non-trivial logic: write it as a Python script under `bin/<name>` (no extension) with `#!/usr/bin/env python3` and `chmod +x`. It becomes available on PATH automatically. Keep zsh wrappers only when shell-specific behavior is needed (e.g. `print -z` to put text on the zle buffer, backgrounding with `& disown`).

### Sourcing `~/.airc` from a script

`~/.airc` is a supported entry point for non-interactive consumers — agent supervisors, launchd
jobs, wrapper scripts — not just for `~/.zshrc`. Two rules keep it that way, and both were
learned by breaking them:

- **Nothing under `.airc.d/` may depend on a symbol defined in `~/.zshrc`.** That file is read
  by interactive shells only, so the dependency is invisible until a script sources `~/.airc`
  alone and gets callers without their callee. Secret injection is therefore `bin/sops-exec`, a
  script, rather than a function in either repo; `~/rc`'s editor wrappers call the same one.
- **`00-path.zsh` appends the mise shims and `~/.local/bin`.** `mise activate` also lives in the
  interactive-only file, so without this a script finds neither `sops` nor `nono` and both
  wrappers fall through to an unsandboxed, keyless command.

Those fallbacks are deliberate (a machine with no secrets still gets a working `nvim`) and
therefore silent. A launcher that cannot tolerate them sets **`AGENT_REQUIRE_SECRETS=1`** and/or
**`AGENT_REQUIRE_SANDBOX=1`**, which turn each into a diagnostic on stderr and exit 78. Prefer
that to trusting PATH: a keyless agent bills the subscription and an unsandboxed one has the
whole filesystem.

## Skills and harness integration

Skill inventory, extension rules, permissions, MCP/tool defaults, plugins, hooks, and GitHub token wiring are in [docs/skills-and-integration.md](docs/skills-and-integration.md).

## Sandbox (nono)

What the sandbox is *for* — the threat model, git and `gh` authentication, why `git push` differs
between sandboxed, raw and interactive contexts, and the known gaps — is
[`docs/security-model.md`](docs/security-model.md). This section is the mechanics.

Every agent CLI runs inside [nono](https://github.com/nolabs-ai/nono), a Seatbelt-based
capability sandbox. The shell wrappers in `.airc.d/` do this transparently — `claude`, `codex`,
`opencode` and `pi` are zsh functions that call `_agent_sandboxed` (`.airc.d/05-sandbox.zsh`),
which wraps the real binary in `nono run -p <agent>-local` *inside* `sops-exec`. Each has a
`<name>-raw` escape hatch that keeps the secret injection but drops the sandbox; use it for
`loadout sync` and anything that must write outside `~/wrksp`.

**`claude` and `codex` route to `-raw` automatically inside `~/ac` and `~/rc`** (the
`AGENT_RAW_DIRS` check in `.airc.d/05-sandbox.zsh`), since work in those repos writes outside
`~/wrksp` by definition. They announce the switch on stderr; `AGENT_FORCE_SANDBOX=1` overrides
it. `pi` and `opencode` have no raw variant and always sandbox.

**Every session is told which mode it is in.** The sandboxed branch exports `AGENT_SANDBOX=1` and
`AGENT_SANDBOX_PROFILE`; `bin/agent-sandbox-status` turns them into a one-paragraph note, which
reaches the model through a `SessionStart` hook for Claude and Codex (`loadout/hooks/`)
and a `sandbox-status` plugin for OpenCode and Pi (`loadout/module-config/`). The global
instructions defer to that note, so keep them free of claims that hold in only one mode.

**Update agents with `bin/agents-update`, from your own terminal.** claude, pi and droid install
into paths the sandbox grants read-only, so their built-in updaters fail inside it (droid reports
only `Update to <version> was skipped.`). The script calls each updater by path, bypassing the
sandboxed wrappers, and updates pi through `mise upgrade` because mise owns that install. It
refuses to run when `AGENT_SANDBOX` is set.

**`~/rc/.zshrc` must not define these four functions.** It sources `~/.airc` first, so a wrapper
there silently overrides the sandboxed one and the sandbox quietly stops applying. It owns the
`nvim` / `mvim` / `neovide` wrappers, which call `bin/sops-exec` off PATH behind a `command -v`
guard, so neither repo depends on the other's shell config.

### Profiles

Profile construction — the `extends` chains over vendor packs, `agent-private.json` for grants that stay out of this public repo, what `agent-common.json` shares, the per-agent grant table, and the droid exception (no vendor pack; keychain login denied, so it authenticates with a sops-held `FACTORY_API_KEY`) — lives in [docs/nono-grants.md](docs/nono-grants.md#profiles). **Pull the packs first** (`nono pull nolabs-ai/{claude,codex,opencode,pi}`); without the pack the profile is inert.

### Gotchas

- `filesystem.deny` cannot subtract an inherited group allow; change the source group or use
  `groups.exclude` instead.
- A nested Seatbelt sandbox is a system-service denial, not a missing path grant. Disable the
  inner sandbox for tools that support it (for example, Chrome needs `--no-sandbox`).
- Exit denials from ordinary config probes are often benign. Read the command's exit status and
  the full nono footer before changing a profile.
- **Test a new nono release against every profile before switching to it.** A release can turn
  formerly ignored profile keys into parse errors, and Claude runs nono with `--silent`, so the
  warnings never reach us; check each profile against the candidate binary and update the vendor
  packs in the same step.
- After `nono update`, run `./sync.sh`, then `bin/nono-audit --check`, and confirm
  `login.keychain-db` stays unreadable under every profile.

The same applies to the skill: `loadout/skills/nono-sandbox/SKILL.md` overrides the pack's copy for all four agents, because `loadout sync --global` writes it into each harness's own skills directory. It carries a `::: opencode` section — OpenCode's version is substantially longer than the one the other three get. Re-run `loadout sync --global` after a pack update to restore it.

## Global agent configuration

The generated global-instruction, Pi, and template-loading details are in [docs/global-agent-configuration.md](docs/global-agent-configuration.md).

## Project templates

Template structure and the rejected alternatives are in [docs/project-templates.md](docs/project-templates.md).

## Secrets Policy

**Never commit API tokens, secrets, or credentials to any file in this repo.** This repo is version-controlled and shared. MCP server configs use `${ENV_VAR}` interpolation for auth — never hardcode tokens.

Dev secrets are SOPS-encrypted and injected into subprocesses by zsh wrappers around the AI CLI tools. Do not enumerate, read, or echo the secrets store from this session — see `~/.claude/CLAUDE.md` "Secrets" for the agent-facing rules.

## Verification Policy

Never claim "best practice", "recommended", "accepted solution", "community consensus", "known bug", "known issue", or "known limitation" without a cited source. If you haven't verified something, say "I believe" or "this might work" - not "this is the way."

**Do NOT say:**
- "This is the accepted approach" → without a source, you don't know this
- "The community recommends" → find a citation or don't claim consensus
- "This is best practice" → according to whom?
- "Known bug" / "known issue" → known by whom? Link the issue or say "I suspect"

When unsure, be explicit: "I think this will work, but I haven't verified it's the recommended approach."

## Build & Check Workflow

- After writing or creating any new file, run the project's formatter before running check-all or lint commands.
- When a typecheck or lint command fails, read ALL errors and fix them in one pass before re-running. Do not fix one error and re-check.
- When moving or renaming files: update imports, barrel/index exports, and clear build caches (e.g., `.next`, `build/`) in the same pass — before re-running checks.
- When changing a shared type or component prop, grep for all consumers and update them before re-running typecheck.
- Do not reflexively re-run a failing command without making changes first. If it failed, something needs fixing.
