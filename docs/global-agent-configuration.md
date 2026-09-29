# Global agent configuration

Each agent's **global** (machine-wide) natural-language guidance — browser automation, secrets handling, git policy, etc. — is generated from a single source of truth: the fragments in **`loadout/instructions/`**. `loadout` assembles them into each agent's global instruction file, the same generate-and-check pattern used for permissions.

**Never hand-edit these generated files** — a lefthook pre-commit hook (`loadout check`) rejects any drift:
- `~/.claude/CLAUDE.md` (Claude; the autonomous profile writes the same path)
- `~/.codex/AGENTS.md`, `~/.pi/agent/AGENTS.md`, `~/.config/opencode/AGENTS.md`, `~/.factory/AGENTS.md` — the shared document every non-Claude agent gets

All five are written directly to those paths; none is staged here or symlinked.

**Only Claude gets its own file.** It needs the `CLAUDE.md` filename, the Jina Web Fetching section, and the autonomous git-policy variant. Every other agent shares one composed document — the content is identical, so there's no reason to branch per-agent until one actually needs something different. (Codex reads global instructions from `~/.codex/AGENTS.md` and Pi from `~/.pi/agent/AGENTS.md`; the destinations differ but point at the same source.)

To change global guidance: edit a fragment in `loadout/instructions/`, then run `loadout sync` (also run automatically by `./sync.sh` and `install.sh`). Each target names its fragments explicitly in its `instructions` list in `loadout.toml`, so the differences that exist are visible in one place — e.g. `web-fetching` (the Jina MCP) is Claude-only because only Claude has that MCP configured; the autonomous profile swaps in the `git-policy.autonomous` fragment. Adding a fragment file does nothing until a target lists it by name; `loadout explain <fragment>` reports which targets use one.

**Why a generator, not native `@imports`:** only Claude Code expands in-file `@path` imports; Codex, OpenCode and Pi have none. A generator is the only DRY approach that works uniformly across every agent.

**OpenCode** gets no file of its own: it reads `~/.claude/CLAUDE.md` as a global-rules fallback. Per OpenCode's docs it treats that file as plain rules and does not expand `@imports` — moot here, since the generated file is already fully expanded. Disable via `OPENCODE_DISABLE_CLAUDE_CODE_PROMPT=1` if ever unwanted.

## Pi

Pi (`@earendil-works/pi-coding-agent`, installed via mise) is wired up like the other non-Claude
harnesses, but through Pi's own mechanisms rather than the generated permission/global pipelines:

- **Global instructions** — Pi loads `~/.pi/agent/AGENTS.md`, symlinked to the shared
  the same composed document Codex gets.
- **Skills** — Pi auto-discovers `~/.agents/skills/` (and `~/.pi/agent/skills/`) by default. That
  first directory is already populated by `install_codex_skills`, so Pi gets the same curated skill
  subset as Codex with no pi-specific config. Skills surface as `/skill:<name>` and via
  progressive disclosure in the system prompt.
- **Permissions** — Pi has none, deliberately. Its core ships no approval layer at all: `--tools`
  scopes which tools exist and `--approve` trusts project-local files, but neither gates an
  individual call. Nothing here supplies one either, so every tool call runs unprompted. That is
  safe only because Pi is sandbox-only — the `pi` wrapper has no `-raw` variant, so nono is always
  the boundary and an approval prompt would add friction without adding containment. **A `pi-raw`
  variant would need this revisited.**
- **MCP servers** — `~/.pi/agent/mcp.json` holds real `mcpServers` definitions, rendered
  directly from `loadout/mcp.toml` (no longer symlinked from this repo). HTTP auth uses `bearerTokenEnv` (the
  variable NAME), so no token is written. It previously imported Claude's registry
  (`{"imports": ["claude-code"]}`), which made Pi's MCP depend on Claude being installed and
  registered — and on `~/.claude.json`, the one file loadout cannot write.
  **Pi caches its resolved server list in `~/.pi/agent/mcp-cache.json` and editing `mcp.json`
  does not invalidate it** — a server added to `servers.toml` stays invisible to Pi until that
  cache is deleted.
- **Model picker** — `loadout/settings/pi.json` sets `enabledModels`, a glob allowlist
  (`provider/id`, minimatch, same format as Pi's `--models` flag) that scopes the `/model` default
  view and Ctrl+P cycling. It does **not** delete models from the "show all" tab. To change which
  models are offered, edit that array; read it there rather than trusting a list quoted here, since
  the `agent-models` skill rewrites it. **Do not** edit `~/.pi/agent/models-store.json` — that is a
  fetched catalog cache Pi overwrites on `pi update`.

**`~/.pi/agent/settings.json` is generated, not symlinked** — that changed when pi settings moved
into loadout. Pi still writes `lastChangelogVersion` and any `/settings` / `/model` change back into
it at runtime, but those writes now land in a generated file and the next `loadout sync` discards
them. A `/model` change you want to keep belongs in `loadout/settings/pi.json`.
