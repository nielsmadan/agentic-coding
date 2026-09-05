# Agentic Coding Config

Version-controlled configuration shared across the AI coding tools I run:
**Claude Code**, **OpenAI Codex**, **OpenCode**, and **Pi**.
One repo holds the skills, hooks, permissions, project templates, and shell glue
for all of them.

Most harness config is rendered in place by **loadout** from the fragments under
`loadout/`. A smaller set of static assets still uses symlinks, including the
nono profiles, `.airc`, and launchd-facing helper binaries.
Treat `loadout.toml` as the ownership manifest: edit the declared source
fragment, never the generated file in a harness's config directory.

## Quick start

```sh
git clone <this-repo> ~/ac
cd ~/ac
./install.sh
```

`install.sh` bootstraps a machine and delegates repeatable reconciliation to
`sync.sh`. Together they:

- render instructions, permissions, MCP definitions, settings, hooks, plugins,
  skills, defaults, and module config into each harness's live paths
- install the remaining static symlinks
- register missing Claude MCP servers and local plugin marketplaces
- optionally add `source ~/.airc` to your `~/.zshrc`

Use `./install.sh --autonomous` to install the broader **autonomous-dev profile**
(permits `git push` and other unattended ops — for machines running headless
agent tasks). Plain `./install.sh` installs the normal profile.

Machine prerequisites (`python3`, the agent CLIs, `npx`/`uvx`/`dart` for some
MCP servers) are **not** auto-installed — set those up separately.

## Repository layout

| Path | What it holds |
|------|---------------|
| `loadout/` | Source fragments for generated instructions, permissions, MCP servers, settings, hooks, plugins, skills, defaults, templates, and module config |
| `loadout.toml` | Manifest selecting and composing those fragments for each harness |
| `codex/` | Codex-specific synchronization helpers and the managed `developer_instructions` source |
| `nono/` | Shared and per-harness nono sandbox profiles installed by symlink |
| `publish/` | Generator and fail-closed manifest for the public skills collection ([nielsmadan/skills](https://github.com/nielsmadan/skills)) |
| `loadout/templates/` | Per-project-type config a project opts into by name (`flutter/`, `react-native/`, `web/`) |
| `.airc` / `.airc.d/` | Shell entry point and per-topic zsh files (PATH, env vars, aliases/functions per tool) |
| `bin/` | Standalone CLI scripts on PATH (`ccmove`, `ccname`, `clcof`) |
| `docs/` | Repo notes |

## The four agents

A single manifest feeds all four tools. Shared shell-command and MCP permissions
are defined once in `loadout/permissions.toml`, while harness-native concerns are
kept in separate slices and composed only at render time:

| Concern | Source | Example generated destination |
|---------|--------|-------------------------------|
| Residual harness settings | `loadout/settings/<name>.json` | `~/.pi/agent/settings.json` |
| Claude hook registrations | `loadout/hooks/*.json` | `~/.claude/settings.json` |
| Enabled plugins / packages | `loadout/plugins/<name>.json` | Claude or Pi settings |
| Scalar model defaults | `loadout/defaults/*.json` | the owned keys in a harness config |
| Extra harness files | `loadout/module-config/<harness>/...` | the matching path below that harness's config directory |

For example, Pi's ordinary settings and package list come from
`loadout/settings/pi.json` and `loadout/plugins/pi.json`; its statusline and
subagent files mirror `loadout/module-config/pi/` beneath `~/.pi/agent/`. These
destinations are generated real files, not repository symlinks. Keeping hooks,
plugins, and settings in distinct slices prevents a residual settings document
from becoming a second owner of generated keys.

Codex keeps mutable state in `~/.codex/config.toml`, so that file is not
symlinked. loadout writes it in place instead, owning only the keys it declares
— `mcp_servers`, `plugins`, `marketplaces` and the model defaults — and leaving
every other user and Codex-managed setting untouched.

## Skills

Skills are reusable `/<name>` workflows — code review, research, debugging,
documentation, security audits, and more. They live under `loadout/skills/`;
invoke one with `/<skill-name>` plus any arguments. loadout renders them to
Claude, Codex, OpenCode, and Pi.

- **Full catalog:** [`loadout/skills/README.md`](loadout/skills/README.md) — every
  skill with arguments and examples. There's also a summary table in
  [`AGENTS.md`](AGENTS.md#skills).

## Permissions

All four agents' shell-command and MCP permissions are **generated** from
`loadout/permissions.toml`. Never hand-edit the live generated files under the
harness config directories — `loadout check --global` reports drift. To change
permissions, edit the source and run:

```sh
loadout sync --global
```

The `/loadout` skill is the normal interface: it edits the narrowest source
fragment and syncs. Global rules live in `loadout/permissions.toml`; a project's
own live in its `loadout/permissions.toml`, with `permissions.local.toml` for
personal rules that are never committed.

See the [Permissions section in `AGENTS.md`](AGENTS.md#permissions) for the full
model (shared vs. agent-native entries, the autonomous profile).

## Project templates

`loadout/templates/<type>/` carries config that belongs to a *kind* of project
rather than every session — permissions, instructions, MCP servers and
project-only skills, in any combination. A project opts in by name:

```sh
loadout init --harness claude    # scaffold loadout/config.toml
loadout template add flutter     # adds templates = ["flutter"]
loadout sync
```

A template is a source at the bottom of the precedence chain, so anything the
project declares itself outranks it. See the
[Project Templates section in `AGENTS.md`](AGENTS.md#project-templates).

## Shell config

`.airc` is sourced from `~/.zshrc` and loads every `*.zsh` under `.airc.d/`.
To extend it:

- **Aliases / functions** → add to the relevant `.airc.d/<topic>.zsh`, or create
  a new topic file.
- **CLI commands** (with flags or non-trivial logic) → add an executable script
  under `bin/`; it lands on PATH automatically.

Reload with `source ~/.airc` (idempotent — re-sourcing won't duplicate PATH
entries).

## Further reading

- [`AGENTS.md`](AGENTS.md) — project instructions, policies, and detailed
  subsystem docs
- [`loadout/skills/README.md`](loadout/skills/README.md) — full skill catalog
- [`templates/`](templates/) — per-project-type config and skills
