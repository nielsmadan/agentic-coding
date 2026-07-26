# Agentic Coding Config

Version-controlled configuration shared across the AI coding tools I run:
**Claude Code**, **OpenAI Codex**, **Google Antigravity** (`agy`), **OpenCode**,
and **Pi**.
One repo holds the skills, hooks, permissions, project templates, and shell glue
for all of them.

Everything is installed by **symlink**, so editing a file here updates the live
config for every tool — no copy step, no drift. Permissions are the exception:
they're *generated* for each agent from a single source of truth.

## Quick start

```sh
git clone <this-repo> ~/ac
cd ~/ac
./install.sh
```

`install.sh` is idempotent and prompts before replacing anything. It:

- generates each agent's permission config from `permissions/permissions.toml`
- symlinks config into `~/.claude`, `~/.codex`, `~/.gemini/antigravity-cli`,
  `~/.opencode`, and `~/.airc`
- installs the curated Codex skill subset into `~/.agents/skills`
- optionally adds `source ~/.airc` to your `~/.zshrc`, wires up the Todoist MCP
  server, and checks that `agy` is on PATH

Use `./install.sh --autonomous` to install the broader **autonomous-dev profile**
(permits `git push` and other unattended ops — for machines running headless
agent tasks). Plain `./install.sh` installs the normal profile.

Machine prerequisites (`python3`, the agent CLIs, `npx`/`uvx`/`dart` for some
MCP servers) are **not** auto-installed — set those up separately.

## Repository layout

| Path | What it holds |
|------|---------------|
| `claude/` | Claude Code config: `skills/`, `hooks/`, `settings.json` (+ `settings.autonomous.json`), `CLAUDE.md` (+ autonomous variant), and `desktop/` (Claude Desktop skills, packaged separately) |
| `codex/` | OpenAI Codex config: managed `config.toml` overlay, permission `rules/`, and curated skills synced to `~/.agents/skills` |
| `antigravity/` | Google Antigravity (`agy`) settings |
| `opencode/` | OpenCode config (`opencode.json`) |
| `pi/` | Pi settings plus the generated `@gotgenes/pi-permission-system` policy |
| `permissions/` | Single source of truth for shell-command and MCP permissions — `permissions.toml` plus `sync.py`, which generates every agent's permission config |
| `templates/` | Per-project-type config + project-only skills (`flutter/`, `react-native/`, `web/`), deployed into projects with `aiconf` |
| `.airc` / `.airc.d/` | Shell entry point and per-topic zsh files (PATH, env vars, aliases/functions per tool) |
| `bin/` | Standalone CLI scripts on PATH (`ccmove`, `ccname`, `clcof`) |
| `docs/` | Repo notes |

## The five agents

A single config feeds all five tools. Shared shell-command and MCP permissions are
defined once in `permissions/permissions.toml` and generated out to each agent;
agent-native settings (tool toggles, MCP entries, skill subsets) live in the
per-agent directories above. Codex, Antigravity, and Gemini CLI pick up Claude's
skills through symlinks rather than separate copies.

Codex keeps mutable state in `~/.codex/config.toml`, so that file is not
symlinked. `sync.sh` merges the table subtrees declared in `codex/config.toml`
into it and preserves all other user and Codex-managed settings.

## Skills

Skills are reusable `/<name>` workflows — code review, research, debugging,
documentation, security audits, and more. There are ~38 of them under
`claude/skills/`; invoke one with `/<skill-name>` plus any arguments.

- **Full catalog:** [`claude/skills/README.md`](claude/skills/README.md) — every
  skill with arguments and examples. There's also a summary table in
  [`AGENTS.md`](AGENTS.md#skills).
- **Codex** gets a curated subset (see `CODEX_SKILLS` in `sync.sh`), shared
  via symlink.
- **Claude Desktop** skills live in `claude/desktop/` and are packaged into zips
  with `claude/desktop/package-skills.sh`, then uploaded through Claude Desktop's
  UI (no automation).

## Permissions

All five agents' shell-command and MCP permissions are **generated** from
`permissions/permissions.toml`. Never hand-edit the generated files
(`claude/settings.json`, `codex/rules/permissions.rules`, `pi/permissions.json`,
etc.) — a pre-commit hook rejects drift. To change permissions, edit
`permissions.toml` and run:

```sh
python3 permissions/sync.py
```

The shared `permission` skill and `aiperm` CLI provide the normal interface:

```sh
aiperm allow --scope local --shell pytest
aiperm allow --scope global --mcp jina/*
aiperm list --scope all
```

Global rules are tracked and regenerated for all harnesses. Local rules are
personal, project-scoped, and stored under `.aiconf/`.

See the [Permissions section in `AGENTS.md`](AGENTS.md#permissions) for the full
model (shared vs. agent-native entries, the autonomous profile).

## Project templates

`templates/<type>/` carries config and skills that belong to a *kind* of project
rather than every session. The CLI verbs (defined in `.airc`):

```sh
aiconf [dir]          # assess a project: install its template, or reconcile drift
aiconf sync [dir]     # bidirectionally sync project edits with its template
aiconf <type> [dir]   # install a specific template (copies real files)
```

Every verb routes to the `/aiconf` skill. It checks whether the project is
configured and installs the detected template if not; otherwise it compares each
deployed artifact against the template and decides per file whether to pull
project changes back into the template, push template updates out, or
semantically merge when both sides moved. See the
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
- [`claude/skills/README.md`](claude/skills/README.md) — full skill catalog
- [`templates/`](templates/) — per-project-type config and skills
