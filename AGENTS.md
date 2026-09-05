# AGENTS.md

This file provides guidance to agentic coding tools working in this repository.

## Repository Overview

This repository contains shared configuration for agentic coding tools. It includes skills, hooks, and permission settings that can be used across multiple projects.

## Structure

- `claude/` - Claude Code specific configuration
  - `settings.json`, `settings.autonomous.json` - **generated in full** (see Permissions below)
  - the hand-maintained half of the two files above lives in `loadout/settings/` (see Permissions below); **edit those, not the generated `settings.json`**
  - `mcp-permissions.json` - **generated** `PermissionRequest` hook policy
  - `CLAUDE.md`, `CLAUDE.autonomous.md` - global Claude guidance (**generated** — see Global Instructions below)
  - `skills/` - Custom skills in `<skill-name>/SKILL.md` format (a few are **generated** — see Multi-Harness Skills below)
  - `hooks/` - Shell scripts triggered by events (e.g., notification when waiting for input)
- `codex/` - OpenAI Codex CLI configuration
  - `rules/` - Permission rules (**generated** — see Permissions below)
  - `developer-instructions.md` - the one `~/.codex/config.toml` key loadout cannot hold,
    written by `sync_config.py` (see Codex Model Defaults below). Model defaults moved to
    `loadout/defaults/codex.json`.
- `pi/` - Pi (`pi-coding-agent`) configuration
  - `settings.json` - symlinked to `~/.pi/agent/settings.json`; holds the `enabledModels`
    allowlist that scopes the model picker (see Pi below). Pi reads global instructions from
    `~/.pi/agent/AGENTS.md` (the shared `global/AGENTS.md`) and auto-discovers skills from
    `~/.agents/skills/`, so those need no pi-specific files.
- `permissions/` - Single source of truth for agent shell-command and MCP permissions
  - `permissions.toml` - the source; edit this
  - `sync.py` - retained entry point only; the global renderers moved to `loadout` (see Permissions below)
- `mcp/` - Single source of truth for **global** MCP server definitions (see MCP Servers below)
  - `servers.toml` - the source; edit this
  - `sync.py` - regenerates every agent's MCP config from the source
- `skills/` - Single source of truth for skills whose text differs per harness
  - `<name>.template.md` - the shared skill body with `{{PLACEHOLDER}}` slots; edit this
  - `sync.py` - renders each harness's `SKILL.md` from the template (see Multi-Harness Skills below)
- `loadout.toml` - the manifest: declares every generated file, its renderer, and its base. **The authority on what is generated** — if a path appears as an `output` here, never hand-edit it.
- `global/` - Single source of truth for each agent's **global** (machine-wide) instructions
  - `fragments/` - shared prose sections (browser automation, secrets, git policy, ...); edit these
  - `AGENTS.md` - **generated** shared file for every non-Claude agent (symlinked to `~/.codex/AGENTS.md` + `~/.pi/agent/AGENTS.md`); see Global Instructions below
- `loadout/templates/<type>/` - Project-type config a project opts into by name (see Project
  Templates below); each may carry `permissions.toml`, `instructions.md`, `mcp.toml` and
  `skills/<name>/`, and need not carry all four
- `.airc` - entry point sourced from `~/.zshrc` (symlinked from `~/.airc`); loads everything under `.airc.d/`
- `.airc.d/` - one `.zsh` file per topic, sourced in glob order
  - `00-path.zsh` puts `bin/` on PATH; `10-env.zsh` sets shared env vars; the rest hold aliases/functions per tool
- `bin/` - standalone CLI scripts on PATH (e.g. `ccmove`, `clcof`); add new ones here rather than as zsh functions. `.airc.d/00-path.zsh` covers interactive shells only — a script that must also run under launchd needs an explicit `~/.local/bin` symlink in `sync.sh`'s `SYMLINKS` (as `jina-fetch` and `sops-exec` have)

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

## Skills

Global skills live in `loadout/skills/<name>/`; every harness surfaces the
available ones with their descriptions, so this file does not restate them. The
human-facing catalog (arguments, examples) is
[`loadout/skills/README.md`](loadout/skills/README.md).

loadout renders each skill to all four harnesses — `~/.claude/skills/`,
`~/.codex/skills/`, `~/.config/opencode/skills/` and `~/.pi/agent/skills/`. Those
are generated directories: edit the source, never the output.

What follows is the part that is *not* discoverable from the skill list itself.

### Extending code-review per language / per project

`code-review` first runs `review-comments --fix` as an unscored cleanup preflight. The review then layers four tiers of checks:

1. **8 language-agnostic aspects** — the default comprehensive set (logic, architecture, security, …); explicit aspect flags select a subset.
2. **Language reviews** — global skills named `review-<language>` in `loadout/skills/`. Auto-invoked when `code-review` detects that language in the scoped files. `review-typescript` and `review-swift` are the current ones. Add a new language by creating `review-<language>/SKILL.md` and adding a row to the detection registry in `code-review`'s Step 3b.5.
3. **Project review** — an *individual project* can define `.claude/skills/review-project/SKILL.md` for checks unique to that codebase. `code-review` calls it only when it exists; projects without one are unaffected. The minimal shape is documented in `code-review`'s "Language & project reviews" section.
4. **Library-use review** — global `review-library-use` checks code against a per-repo `library-use` reference (docs-derived, version-specific correct-usage conventions). Auto-invoked when the repo has `.claude/skills/library-use/SKILL.md`, which the global `library-docs` skill generates and refreshes. Trio: `library-docs` (build/refresh) → `library-use` (per-repo reference) → `review-library-use` (audit).

### Adding a skill

Drop the skill at `loadout/skills/<name>/SKILL.md` and run `loadout sync --global`.
The directory *is* the declaration — there is no list to add it to, and it reaches
all four harnesses.

One optional hookup: add an entry to
[`loadout/skills/README.md`](loadout/skills/README.md) (the human-facing catalog —
agents read the skill's own `description:` field, so that frontmatter is what
actually needs to be good).

Supporting files (`references/`, `scripts/`) are copied byte-for-byte with their
mode preserved, so an executable script stays executable. `__pycache__` and other
build artifacts are skipped.

### Multi-harness skills

A skill whose text must differ per harness marks the differing parts inline. Two
skills do today, for different reasons.

`code-review` is the biggest case: dispatch and sub-agent instructions differ
between the claude/codex/opencode family and pi, which fans out through a
`workflowScript` instead of repeated tool calls. `nono-sandbox` is the other
shape: OpenCode carries a substantially longer version, so the two documents are
wrapped whole. (`skill-creator` shows `:::` lines too, but only inside a fenced
example documenting the syntax — they render as-is everywhere.)

Marked sections wrap whole blocks:

```markdown
::: claude
- **Codex** blocks on "Reading additional input from stdin…" unless stdin is closed.
:::
::: codex opencode
- **Claude** runs non-interactively in print mode (`claude -p`).
:::
```

A marker never sits *inside* a fenced code block — to vary a code example, mark the
whole fence twice. Adjacent blocks must have no blank line between them, or that
line reaches every harness.

Frontmatter is YAML, so a `:::` there would be data. Per-harness *values* use a
block keyed by harness instead, merged over the shared keys and stripped from the
output:

```yaml
name: nono-sandbox
description: Decide whether a failure is actually a nono sandbox denial…
opencode:
  description: Diagnose and resolve permission denials when opencode runs…
```

Unmarked skills — 50 of 52 — pass through untouched, so the mechanism costs nothing
until used. `loadout check --global` reports any drift, and `loadout sync` refuses
to overwrite a hand-edited output rather than discarding it.

Two constraints on the generator: the `<!-- GENERATED ... -->` banner is inserted *below* the YAML
frontmatter (anything above the opening `---` leaves the frontmatter unparsed, and the skill then
advertises the banner as its description), and each advisor CLI needs a matching allow rule in
`loadout/permissions.toml` — `codex exec -s read-only`, `opencode run`, `claude --tools`.

### Repo-local skills

`.claude/skills/<name>/` holds skills that only make sense *inside this repo* —
they edit this repo's own files, so rendering them globally would be noise in
every other project. They are not part of the loadout pipeline: no sync step, no
`loadout check` coverage, and Claude Code picks them up directly.

**To reach Codex too, symlink it into `.codex/skills/`** — that is Codex's
project-local skill directory, discovered relative to the project root, the same
way `.claude/skills/` is for Claude Code:

```
ln -sfn ../../.claude/skills/<name> .codex/skills/<name>
```

One source of truth, two harnesses, still scoped to this repo — `~/.codex/skills/`
(the global directory loadout renders into) stays untouched, so the skill does not
appear in unrelated projects. Verified against codex-cli 0.147.0.

- **`agent-models`** — picks the low / mid / high-main / high-fallback OpenRouter
  models and writes them into every file that pins a model id (`pi/settings.json`,
  `loadout/settings/opencode.json`, `clor` in `.airc.d/claude.zsh`, the `ocs`
  alias, the `occli` backend, and the two `second-opinion` advisors). Ranks
  candidates from Artificial Analysis by agentic index vs cost per task; never
  picks Grok, and prefers non-frontier-lab models on a tie.

  The Artificial Analysis models page is JS-rendered — fetchers return prose with
  no numbers. `scripts/rank_models.py` parses the full per-model dataset out of
  the RSC payload (`self.__next_f`) the page server-renders, then resolves exact
  OpenRouter ids from `openrouter.ai/api/v1/models`. Model *names* collide across
  builds (`deepseek/deepseek-v4-pro` is the 0423 build, not the 0813 one), so ids
  always come from that API, never from a name.

## Permissions

Shell-command and MCP permissions for all four agents (Claude, Codex, OpenCode, Pi) are generated from a single source of truth: **`loadout/permissions.toml`**. The renderers live in **`loadout`** (a separate tool, installed on `PATH`); `loadout.toml` declares which file each one writes.

**Never hand-edit a generated file** — a lefthook pre-commit hook (`loadout check --global`) rejects any drift. `loadout.toml` is the authority on which files those are; every path appearing there as an `output` or a `destination` is generated. Nearly all of them are now written **straight to the machine path the agent reads** and are not staged in this repo at all — `~/.claude/settings.json`, `~/.codex/rules/permissions.rules`, `~/.codex/config.toml` and the rest. One exception lands here: `loadout/defaults/codex.owned`, the record of which keys loadout manages in `config.toml` rather than a config file itself.

**Some outputs are only half generated.** Where a file also holds hand-maintained settings, that half lives in a **base document** which is an input and is never written:

| edit this | to change | which is generated into |
|---|---|---|
| `loadout/permissions.toml` | any shell or MCP rule, on every agent | all seven permission files |
| `loadout/settings/claude.json` | hooks, statusLine, model, env, `permissions.defaultMode` — for **both** profiles | `~/.claude/settings.json` |
| `loadout/settings/claude-afk.json` | the default profile's `env.CLAUDE_AFK_TIMEOUT_MS` only | `~/.claude/settings.json` under the default profile |
| `loadout/bases/opencode.base.json` | `model`, `provider`, `$schema` | `~/.config/opencode/opencode.json` |

`~/.claude/settings.json` in particular is generated **in full** — it looks hand-maintained and is not. Putting a hook there instead of in `loadout/settings/claude.json` loses the edit at the next sync. Claude Code writing to it itself no longer gets silently merged either: `loadout sync` stops and prints the added lines so you can move them into the base.

To change permissions: edit the source, then run `loadout sync --global` (also run by `./sync.sh` and `./install.sh`). `loadout explain <fragment>` reports where an instruction fragment came from and which targets use it. Deeper reference — per-harness matcher semantics, pattern shapes, known upstream bugs — lives in the loadout repo under `docs/reference/`, and is only needed when changing loadout itself.

Use `/loadout` to change permissions. Global rules live in `loadout/permissions.toml`;
a project's own live in its `loadout/permissions.toml`, with `permissions.local.toml` for
personal rules that are never committed. `[shell]` and `[mcp]` entries go to all four agents; `[claude.extra]` / `[opencode.extra]` hold remaining
tool-native entries with no cross-agent equivalent. Codex's token matcher can't express legacy
shell glob entries (those ending in `*`), so they fall through to its normal approval prompt.

`[mcp]` here is *policy* — which tools of a server may be called. Which servers exist at all is
`loadout/mcp.toml` (see MCP Servers below); the two sources are edited independently.

**Auto-mode gotcha:** Claude Code's auto-mode classifier blocks writes to `settings.json` files (so it blocks `loadout sync`, which regenerates them) and hard-blocks any command containing the string `--dangerously-skip-permissions`. In default mode these only prompt. An explicit `Bash` allow-rule is honored *before* the classifier in every mode — the sanctioned way to let a specific such command through (vs. obfuscating the flag, which is evasion).

### Autonomous-dev profile

For machines that run autonomous dev tasks (which must `git push` etc. without a human in the loop) there is a second **Claude-only** profile built around auto mode's classifier. Only one of the two renders on any machine: `[permissions.claude]` and `[permissions.claude-autonomous]` declare `profile = "default"` and `profile = "autonomous"` and take turns writing `~/.claude/settings.json`. They share a renderer, differing by base document and by the autonomous one's `rules = []`, which selects no rules at all. The autonomous variant keeps `defaultMode: "auto"` but has **empty `allow` / `deny` / `ask`** so the classifier judges every tool call. Clearing `deny` is what lets `git push` and the other destructive-git ops through (deny overrides every mode, including auto); the `allow` / `ask` lists are dropped so nothing pre-empts or blocks the classifier (an `ask` would also hang a headless run). `instructions.claude-autonomous` is the matching global-guidance variant whose Git Policy permits autonomous git ops; it takes turns writing `~/.claude/CLAUDE.md` the same way. Both are **generated** from shared fragments (see Global Instructions below), so they never drift — the autonomous variant differs only by pulling the `git-policy.autonomous` fragment instead of `git-policy`.

Select the profile with `./install.sh --autonomous` or `./sync.sh --autonomous`, which record it in `~/.config/loadout/config.toml`; `loadout sync --global` then renders whichever profile is named there. `--normal` switches back, and editing that file by hand does the same. The other three agents (Codex, OpenCode, Pi) get the same config under either profile.

## MCP Servers

Which MCP servers **exist** machine-wide comes from a single source of truth: **`loadout/mcp.toml`**. Which of their *tools* may be called is the separate `[mcp]` section of `loadout/permissions.toml` — definitions there, policy here. The two sources name servers independently, so adding one does not grant it any permissions.

loadout renders both, and for Codex it renders them **together**: definitions and approval policy share the `[mcp_servers.<name>]` table, so one renderer emits both. Two writers would declare that table twice and Codex would refuse to parse its own config.

**Never hand-edit these generated files** — a lefthook pre-commit hook (`loadout check --global`) rejects any drift:
- `$CLAUDE_CONFIG_DIR/.claude.json` (the `mcpServers` key only; the ~100 keys beside it are Claude's own runtime state and are left untouched)
- `~/.codex/config.toml` (`[mcp_servers.*]`, written directly; loadout owns that key and leaves the rest of the file alone)
- `~/.config/opencode/opencode.json` (the `mcp` key only)
- `~/.pi/agent/mcp.json` (`mcpServers`, the shape `pi-mcp-adapter`'s `ServerEntry` takes — written directly, no longer symlinked from this repo)

A `transport = "http"` entry takes `url` plus an optional `auth_env_var`; `transport = "stdio"` takes `command`, optional `args`, and an optional `[<name>.env]` table. **Only ever record the env var's NAME** — each harness has its own interpolation syntax (`${VAR}` for Claude, `{env:VAR}` for OpenCode, `bearer_token_env_var` for Codex, `bearerTokenEnv` for Pi), and loadout refuses a server whose keys it does not recognise rather than silently rendering one that connects unauthenticated.

**Claude Code was the exception until 2026-09-05.** `$CLAUDE_CONFIG_DIR/.claude.json` is its
only user-scope MCP store and is runtime state (session history, project entries, caches), so it
cannot be symlinked — but it does carry a plain top-level `mcpServers` key, and loadout now owns
exactly that one, leaving every other byte alone (the same declared-ownership mechanism as
`~/.codex/config.toml`, with a JSON applier instead of a TOML one).

That closed a real defect. The old path staged a document and fed it to
`claude mcp add-json --scope user`, which has no overwrite flag — so a changed url or args in
`loadout/mcp.toml` silently did not propagate, and a removed server stayed registered. Editing
`mcp.toml` and running `./sync.sh` now does what it looks like it does.

**Per-harness quirks worth knowing:** OpenCode's local servers take a single `command` array combining command and args (not separate fields).

**`~/.config/opencode/opencode.json` has one owner now.** loadout writes both the `mcp` key and `permission`, composing them into one document. It used to have two — `mcp/sync.py` owned `mcp` and loadout carried it across with `preserve = ["mcp"]`, which is why sync order was load-bearing. Both are gone: loadout generates that key, so `preserve` would name a generated key and loadout refuses it outright.

Project-scoped MCP servers are a different mechanism: those live in a project's own `.mcp.json`, rendered from a project's own `loadout/mcp.toml` and from any template it declares (see Project Templates).

## Codex Model Defaults

Codex's default model and reasoning effort come from **`loadout/defaults/codex.json`**, rendered
into `~/.codex/config.toml` by loadout's `defaults` slice (`defaults = "codex"` under `[codex]` in
`loadout.toml`). Edit that file and re-run `./sync.sh`; a hand edit to `~/.codex/config.toml` is
reverted on the next sync, and `loadout check --global` reports the drift.

**Only the keys the fragment names are touched** — currently `model` and
`model_reasoning_effort`. `plan_mode_reasoning_effort` is deliberately not among them and stays
hand-maintained. Named keys are replaced where they already sit, so Codex's own `[projects."…"]`
trust entries, the nono block, `developer_instructions` and the `[mcp_servers.*]` tables all
survive. Nested tables are rejected: this is model defaults, not a second home for everything in
`config.toml`.

**The slice is opt-in, and it strips every key it manages.** A machine that never declares it
never has its hand-maintained Codex settings touched.

**Removal works, and that needs a record.** The key names here are yours, not a set loadout could
enumerate, so ownership is *derived* — and a derived set cannot say a key was ever managed once it
leaves the fragment. loadout therefore keeps `loadout/defaults/codex.owned` beside the fragment:
the union of what it wrote last time and what it writes now is what gets stripped. That file is
generated and committed. Edit the fragment, never the record; `loadout check --global` reports a
record that disagrees with it. See loadout's
[ADR 0017](https://github.com/nielsmadan/loadout/blob/main/docs/decisions/0017-ownership-may-be-declared-instead-of-derived.md).

**Nothing reserializes `~/.codex/config.toml`, and that is the design.** Both loadout's surgery and
this repo's `codex/sync_config.py` work line-wise, using `tomllib` only to validate the result. The
comments, the nono block and the project tables survive because no code path touches those bytes,
not because a writer preserved them. Do not "improve" either into a parse-mutate-serialize round
trip: that trades untouched for preserved-if-the-library-is-careful, and adds a dependency to a
script `install.sh` runs on a fresh machine.

**`codex/sync_config.py` survives for exactly one key.** Everything else it used to merge —
`[mcp_servers.*]`, `[plugins.*]`, `[marketplaces.*]`, the model defaults — is loadout's now. What
remains is `developer_instructions`, which loadout cannot hold: it is a multi-line TOML string, and
loadout's surgery works line-wise over top-level scalars. The nono codex pack keeps re-injecting
its own copy, so something must keep undoing that.

**`publish/` generates the public skills collection.** `publish/sync.py` renders the
`publish`-classified skills from `loadout/skills/` into
[nielsmadan/skills](https://github.com/nielsmadan/skills) — a Claude Code plugin
marketplace and `npx skills` collection; a workflow in that repo runs it hourly.
`publish/skills.toml` classifies every skill into a README group under `[groups]` (published) or into `private`, fail-closed:
the pre-commit hook runs `--check-manifest --check-sources` on every commit, so an
unclassified skill or a personal string (`~/ac`, `/Users/nielsmadan`, …) in a
publishable source rejects the commit — even one that seems unrelated. Run it as a
script path (`python3 publish/sync.py`), never `python3 -m publish.sync`: `-m` puts
the repo root on `sys.path`, where the `loadout/` config directory shadows the
installed `loadout` package. The `loadout` package is a `uv tool` install, not
importable from system Python — only `--out` (render) needs it; the checks and the
tests (`python3 -m unittest publish.test_sync`) run without it.

**Codex validates none of this.** `model_reasoning_effort = "bogus"` is accepted silently and
reported as the session's effort; a wrong value fails server-side at first use. The published
[config reference](https://learn.chatgpt.com/docs/config-file/config-reference) also lags the
binary — it lists `minimal | low | medium | high | xhigh`, while codex-cli 0.149.1 carries `max`
and `ultra` as well. Verify a new value by running `codex exec` once and reading the effort it
reports back.

`codex/test_sync_config.py` covers what is left, including the empty-target case: rendering was not
idempotent there, and a populated target hides it because it reuses what is on disk. It also pins
that our block *replaces* an injected one rather than sitting beside it — two
`developer_instructions` keys is invalid TOML.

## Local Claude Plugins

A plugin developed locally (`mouthfeel`, at `~/wrksp/oss/mouthfeel`) is wired up in **two halves with two owners**, and they must agree:

- **Enablement** — `enabledPlugins` in `loadout/settings/claude.json`, rendered into the generated `~/.claude/settings.json`. Without an entry there, `claude plugin enable` writes the key at runtime and the next `loadout sync` discards it, silently disabling the plugin.
- **Marketplace registration** — `sync.sh`'s `sync_claude_plugins`, driven by the `LOCAL_MARKETPLACES` array. `~/.claude/plugins/known_marketplaces.json` is an install registry Claude rewrites itself (install paths, timestamps), so loadout deliberately does not render it — the same constraint as `.claude.json` for MCP servers. Add-only: if the built path moves, `claude plugin marketplace remove <name>` and re-run.

**`enabledPlugins` lives in the settings base only because this repo declares no `plugins` slice.** loadout has one, and it assigns `enabledPlugins` unconditionally; composition is residual-first, so the moment `loadout.toml` gains `[claude] plugins = [...]` the slice wins and the settings-base copy is overwritten with no message. If you declare one, move the entry into a plugins fragment at the same time.

Reload after a source change is `npm run dev:claude` in the plugin repo: it stamps a fresh version into `dist/claude/mouthfeel/.claude-plugin/plugin.json`, then runs `claude plugin update` and `claude plugin enable`. The version stamp is what stops Claude serving the cached copy. Nothing sandbox-specific is needed — `~/wrksp` and `~/.claude/plugins` are both granted.

## Hooks

Event-triggered shell scripts live in `claude/hooks/` and are wired in under the `hooks` key of **`loadout/settings/claude.json`** — not `~/.claude/settings.json`, which is generated in full and will discard the edit at the next `loadout sync`. When adding one:

- **Make it executable (`chmod 755`).** A non-executable hook is silently skipped — the event fires as if no hook existed. Git preserves mode `100755` once set.
- **Both profiles get it automatically.** They compose the same `loadout/settings/claude.json` fragment — `claude` for autonomous, `claude` + `claude-afk` for default — so a hook added there reaches both. The overlay exists only for `env.CLAUDE_AFK_TIMEOUT_MS`, which is default-only. Run `loadout sync` afterwards.
- **To auto-approve an MCP tool's permission prompt, use a `PermissionRequest` hook returning `decision.behavior: "allow"`** — a `PreToolUse` hook returning `permissionDecision: "allow"` does NOT suppress the prompt. `PermissionRequest` is the only event that fires in every mode, including plan mode and subagents. Since Claude Code's plan-mode rework (~v2.1.198) classifies each call read-only per-call, opaque third-party MCP tools prompt in plan mode regardless of their `mcp__*` allow rule. `auto-approve-mcp.sh` handles this generically from the generated global and project-local MCP policy while preserving deny → ask → allow precedence.

## GitHub tokens

`gh` authenticates with read-only fine-grained PATs from the sops store — there is no
write-capable GitHub credential on this machine, and `gh auth logout` removed the keyring one.
Writes fail with `403 Resource not accessible by personal access token`.

Fine-grained PATs are scoped to **one resource owner**, so a single token cannot cover both a
personal account and an organisation. `GH_TOKEN` holds the `nielsmadan` token;
`GH_TOKEN_<OWNER>` holds one per organisation (`GH_TOKEN_QUANTUMCRAFTIO` today). `bin/gh` picks
the right one from the repo owner — read off `-R owner/repo`, a positional `owner/repo`, a
`repos/owner/…` API path, or the origin remote of the working directory — and execs the real
`gh`.

It is wired in twice because neither mechanism covers both contexts:

- **Inside the sandbox**, `_agent_sandboxed` puts `~/ac/bin` first on `PATH`, so the shim wins.
  A shell function would not exist there at all: shell configs are in nono's permanent deny
  group, so `~/.zshrc` never loads.
- **In an interactive shell**, PATH order cannot win — mise re-prepends its own bin directories
  on every prompt, leaving `~/ac/bin` far down the list. The `gh()` function in
  `.airc.d/gh.zsh` outranks PATH entirely.

Adding an organisation means adding `GH_TOKEN_<OWNER>` to sops; no code change. Note the
`quantumcraftio` org caps fine-grained PAT lifetime at 366 days, so that token needs annual
rotation.

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

**`~/rc/.zshrc` must not define these four functions.** It sources `~/.airc` first, so a wrapper
there silently overrides the sandboxed one and the sandbox quietly stops applying. It owns the
`nvim` / `mvim` / `neovide` wrappers, which call `bin/sops-exec` off PATH behind a `command -v`
guard, so neither repo depends on the other's shell config.

### Profiles

`nono/<agent>-local.json` is symlinked to `~/.config/nono/profiles/` by `sync.sh`. Each extends
two parents — the vendor pack and our shared overlay:

```json
{ "extends": ["nolabs-ai/codex", "agent-common"] }
```

**Pull the packs first** (`nono pull nolabs-ai/{claude,codex,opencode,pi}`); without
the pack the profile is inert. Multi-parent `extends` unions the grants of both.

`nono/agent-private.json` is the escape hatch for grants that should not be in this **public**
repo — client or employer paths, anything identifying. It is gitignored, every `<agent>-local`
profile extends it, and `sync.sh` creates an empty one when absent so a fresh clone still works.
Put machine-specific grants there, not in `agent-common.json`.

`nono/agent-common.json` holds everything the four share: `~/wrksp` read+write, read on `~/ac`
(the agents' own config lives there behind symlinks), mise installs, the colima docker socket, the
agent-browser socket directory, and the Chrome-for-testing Seatbelt rules. Change a shared grant
there, not five times over. The per-agent files hold only what one agent needs:

| profile | extra grant | why |
|---|---|---|
| `claude-local` | read `~/.local/share/claude` | |
| `opencode-local` | read-file `~/.claude/CLAUDE.md`, read `~/.claude/skills` | opencode falls back to Claude's global rules and skills |

### Gotchas

- **`filesystem.deny` does not override an inherited group allow** ([nono#727](https://github.com/nolabs-ai/nono/issues/727)) — nothing can be *subtracted* from a base profile, only added.
- **Nono blocks sandbox re-initialization** under the profile, so anything that starts its own Seatbelt sandbox must be told not to — Chrome needs `--no-sandbox` under `agent-browser`. It is usually a spawned process rather than the agent, and nono reports it as the system service `forbidden-sandbox-reinit`. Measured: `nono run -p codex-local -- sandbox-exec -p '(version 1)(allow default)' /bin/echo hi` fails with exit 71 while the same command outside `nono run` succeeds. The denial names no path, so nono's own `--allow <path>` suggestion cannot apply to it.
- **Docker needs two grants plus `DOCKER_HOST`.** All of `~/.docker` sits in nono's permanent deny group, so each path needs `bypass_protection` as well as a grant. `DOCKER_HOST` (set by the wrapper) is enough for the plain `docker` CLI, but not for `docker compose`: the plugin is discovered via `config.json`'s `cliPluginsExtraDirs` (without it, `docker compose -f …` degrades to `docker -f …` and fails with `unknown shorthand flag: 'f'`), and compose resolves the daemon through `contexts/` rather than `DOCKER_HOST`. Granted: `config.json`, `contexts`. Neither holds a secret — `credsStore` is `osxkeychain`, so the registry credential lives in the keychain, which stays denied. On this machine the compose plugin lives in homebrew's directory, so `~/.docker/cli-plugins` does not exist and granting it only produced a startup warning; a machine that does keep plugins there would need it back.
- **`~/.claude.json` lives inside `~/.claude`, not `$HOME`.** `.airc.d/10-env.zsh` exports `CLAUDE_CONFIG_DIR=$HOME/.claude`, which relocates that file into the directory Claude already owns. Claude writes it by creating `.claude.json.tmp.<random>` and renaming; a random suffix in `$HOME` matches no grant, so the write was denied ([nono#1481](https://github.com/nolabs-ai/nono/issues/1481), open). Inside `~/.claude` the directory grant covers it. The variable is exported globally rather than in the sandbox wrapper so `claude` and `claude-raw` share one store. `~/.claude.json` and its lock file have been removed from `$HOME` entirely; anything launching Claude Code without the variable will create a fresh empty one there rather than silently diverging from the real store.
- **No agent has keychain access, and TLS does not need it.** This took two mistakes to get right. Our profiles carried a narrow `read_file` grant on `login.keychain-db`, which looked like the whole story; underneath it the vendor packs' groups (`claude_code_macos`, `codex_macos`) and the `nolabs-ai/opencode` profile granted the keychain **read+write**, and `security show-keychain-info` worked from inside the sandbox against an unlocked keychain. The narrow entry was in fact *narrowing* the group grant, so removing it alone made `login.keychain-db` writable. The grants are dropped at their source instead: `claude-local` no longer includes `claude_code_macos` (its only non-keychain grant, the URL handler app, is re-added explicitly), `codex-local` uses `groups.exclude` on `codex_macos`, and `opencode-local` reproduces the pack profile without its `read_file` entry. `groups.exclude` works where `filesystem.deny` cannot — a deny does not override an inherited grant ([nono#727](https://github.com/nolabs-ai/nono/issues/727)), and that was measured here too. Codex's Rust TLS stack read trust settings from that keychain, which is why removing it once produced `invalid peer certificate: UnknownIssuer`; `SSL_CERT_FILE=/etc/ssl/cert.pem` in the sandbox wrapper supplies the same public roots and all four agents reach the network with the keychain fully denied. A CA installed **only** in the login keychain — a corporate MITM root, a local dev cert — will not be trusted by sandboxed agents.
- **`nono why` misreports grants inside the built-in keychain protection.** Measured on 0.72.0: with `read_file` on `$HOME/Library/Keychains/login.keychain-db`, `nono why` says `DENIED / filesystem_deny` while `nono run` reads the file; with no grant at all the read fails, so the grant is what opens the path and the diagnostic does not account for it. Adding `bypass_protection` changes nothing in either direction. This is **not** a general `bypass_protection` blind spot — for `~/.netrc` the diagnostic tracks the runtime exactly (grant alone → both deny, grant + `bypass_protection` → both allow), as do `filesystem.deny` rules written in the profile or inherited through `extends`. Where the two disagree, believe the sandbox; trusting `nono why` here has already cost one load-bearing grant.
- **`deny_credentials` paths need `bypass_protection`, not just a grant.** `~/.npmrc` and `~/.netrc` sit in nono's permanent deny group: a `read_file` entry alone still yields `filesystem_deny`, and only adding the path to `bypass_protection` opens it. Weigh that against exfiltration before opening one: sandboxed agents have open outbound network, so a readable credential file is an exfiltratable one.
- **Benign denials are normal.** opencode probes `/Users`, `~/.config` and friends looking for config as it walks up from the workdir. Reported at exit and not worth granting.
- **The claude and codex packs write into generated files.** The claude pack `json_merge`s `enabledPlugins` into `~/.claude/settings.json`, which is why `nono@nolabs-ai` is in `loadout/settings/claude.json`. The codex pack appends a `toml_block` to `~/.codex/config.toml`; despite its `position: "top"` it lands at the end of the file, where its top-level `developer_instructions` key gets absorbed into the last table (`[mcp_servers.jina]`) and `codex/sync_config.py` then strips it. The block's `developer_instructions` text is **replaced with ours** by `codex/sync_config.py`, sourced from `codex/developer-instructions.md` and inserted above the first table (a top-level key after a table header is absorbed into it). A `nono update` restores the pack's copy; the next `./sync.sh` overwrites it again, so this self-heals — the pack's version tells Codex to treat any `Operation not permitted` as a nono boundary and to offer `nono run --allow` / `nono profile promote`, which produced four false denial reports in a day. Ours follows `loadout/skills/nono-sandbox/SKILL.md`, the canonical guidance — the published copy of the skill carries no personal paths, while this local copy keeps the machine-specific ones. **After a `nono update`, run `./sync.sh`** — it restores the instructions.

The same applies to the skill: `loadout/skills/nono-sandbox/SKILL.md` overrides the pack's copy for all four agents, because `loadout sync --global` writes it into each harness's own skills directory. It carries a `::: opencode` section — OpenCode's version is substantially longer than the one the other three get. Re-run `loadout sync --global` after a pack update to restore it.

## Global Instructions

Each agent's **global** (machine-wide) natural-language guidance — browser automation, secrets handling, git policy, etc. — is generated from a single source of truth: the fragments in **`global/fragments/`**. `loadout` assembles them into each agent's global instruction file, the same generate-and-check pattern used for permissions.

**Never hand-edit these generated files** — a lefthook pre-commit hook (`loadout check`) rejects any drift:
- `claude/CLAUDE.md` and `claude/CLAUDE.autonomous.md` → symlinked to `~/.claude/CLAUDE.md`
- `global/AGENTS.md` → symlinked to `~/.codex/AGENTS.md` (Codex) and `~/.pi/agent/AGENTS.md` (Pi)

**Only Claude gets its own file.** It needs the `CLAUDE.md` filename, the Jina Web Fetching section, and the autonomous git-policy variant. Every other agent shares one `global/AGENTS.md` — the content is identical, so there's no reason to branch per-agent until one actually needs something different. (Codex reads global instructions from `~/.codex/AGENTS.md` and Pi from `~/.pi/agent/AGENTS.md`; the destinations differ but point at the same source.)

To change global guidance: edit a fragment in `global/fragments/`, then run `loadout sync` (also run automatically by `./sync.sh` and `install.sh`). Each target names its fragments explicitly in `loadout.toml`'s `order` list, so the differences that exist are visible in one place — e.g. `web-fetching` (the Jina MCP) is Claude-only because only Claude has that MCP configured; the autonomous profile swaps in the `git-policy.autonomous` fragment. Adding a fragment file does nothing until a target lists it by name; `loadout explain <fragment>` reports which targets use one.

**Why a generator, not native `@imports`:** only Claude Code expands in-file `@path` imports; Codex, OpenCode and Pi have none. A generator is the only DRY approach that works uniformly across every agent.

**OpenCode** gets no file of its own: it reads `~/.claude/CLAUDE.md` as a global-rules fallback. Per OpenCode's docs it treats that file as plain rules and does not expand `@imports` — moot here, since the generated file is already fully expanded. Disable via `OPENCODE_DISABLE_CLAUDE_CODE_PROMPT=1` if ever unwanted.

## Pi

Pi (`@earendil-works/pi-coding-agent`, installed via mise) is wired up like the other non-Claude
harnesses, but through Pi's own mechanisms rather than the generated permission/global pipelines:

- **Global instructions** — Pi loads `~/.pi/agent/AGENTS.md`, symlinked to the shared
  `global/AGENTS.md` (same file as Codex).
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
- **Model picker** — `pi/settings.json` (symlinked to `~/.pi/agent/settings.json`) sets
  `enabledModels`, a glob allowlist (`provider/id`, minimatch, same format as Pi's `--models` flag)
  that scopes the `/model` default view and Ctrl+P cycling. It does **not** delete models from the
  "show all" tab. To change which models are offered, edit the `enabledModels` array. **Do not** edit
  `~/.pi/agent/models-store.json` — that is a fetched catalog cache Pi overwrites on `pi update`.
  Current scope: the GPT-5.6 Codex ladder (`gpt-5.6-luna`/`-terra`/`-sol`, default `-terra`) plus a
  curated openrouter spread (`z-ai/glm-5.2`, `minimax/minimax-m2.5`, `deepseek/deepseek-v4-flash`,
  `qwen/qwen3-coder-next`, `qwen/qwen3-coder:free`).

Unlike the other harnesses' settings files, `pi/settings.json` is runtime-mutable: Pi writes
`lastChangelogVersion` (on upgrades) and any `/settings` / `/model` changes back through the symlink
into the repo file, so expect the occasional small diff to commit or discard.

## Project Templates

`loadout/templates/<type>/` holds config that belongs to a *kind* of project rather than to
every session. `flutter/` carries the Flutter MCP servers (`mcp.toml`), the permissions they
need (`permissions.toml`), an instructions block (`instructions.md`) and project-only skills
(`skills/<name>/`). A template need not carry all four — `railway/` is skills only.

Keeping them here version-controls the config centrally without making it global: a template
reaches only a project that asks for it by name, so a bundled skill never pollutes sessions in
unrelated projects.

A project opts in:

```
loadout init --harness claude    # scaffold loadout/config.toml
loadout template add flutter     # adds templates = ["flutter"]
loadout sync
```

A template is a **source**, sitting at the bottom of the precedence chain — anything the project
declares itself outranks it — and it merges through each slice's own operator, so no template-
specific merge rule exists. All four artifact types project scope has flow through it:
permissions, instructions, skills and MCP server definitions.

Declared templates (resolved from `~/ac`) update everywhere on the next `loadout sync`. A
template can instead be **vendored** into a project's own `loadout/templates/<name>/` so the
repo stands alone for contributors who don't run loadout; `loadout template sync` compares a
vendored copy against its origin by content hash and refuses rather than overwriting local
edits.

Project-only skills live *inside* their template (`loadout/templates/<type>/skills/<name>/`),
not in `loadout/skills/`, so they are never rendered globally. Moving a skill between the two
changes where it renders — but **nothing prunes**: `loadout sync` only writes the paths it
renders, so the copies already written under `~/.claude/skills/`, `~/.codex/skills/`,
`~/.config/opencode/skills/` and `~/.pi/agent/skills/` must be deleted by hand.

Templates cover config only; machine prerequisites (e.g. `npx`, `uvx`, `dart` for the Flutter
MCP servers) must be installed separately.

**`aiconf` and `templates/deploy.py` were retired**; loadout's template mechanism replaced them.
Projects deployed by the old system keep working — their files are plain and still read — but
are no longer managed. Migrate one by running the opt-in above, then `git rm --cached` whatever
loadout now generates (`init` gitignores those paths but does not untrack them). Delete only
`.aiconf/` entirely — both `aiconf` and `aiperm`, which wrote the rest of it, are retired.

### Considered but not bundled

- **`chrome-devtools-mcp`** (Chrome DevTools for Agents v1, May 2026) — Chrome team's MCP
  server with Lighthouse audits, performance traces, heap snapshots, network/CPU throttling,
  Chrome extension dev, WebMCP debugging. Complements the `web` template's `agent-browser`
  (driving the page) with DevTools-grade *inspection* of the page. Not bundled by default
  because most web projects don't need it day-to-day and both speak CDP — running both
  against the same Chrome requires pointing chrome-devtools-mcp at agent-browser's instance
  via `--browser-url`, which is fiddly enough to opt into per-project. Install as a Claude
  Code plugin: `/plugin install chrome-devtools-mcp@chrome-devtools-plugins` after
  `/plugin marketplace add ChromeDevTools/chrome-devtools-mcp`.

## Secrets Policy

**Never commit API tokens, secrets, or credentials to any file in this repo.** This repo is version-controlled and shared. MCP server configs use `${ENV_VAR}` interpolation for auth — never hardcode tokens.

Dev secrets are SOPS-encrypted and injected into subprocesses by zsh wrappers around the AI CLI tools. Do not enumerate, read, or echo the secrets store from this session — see `~/.claude/CLAUDE.md` "Secrets" for the agent-facing rules.

## Git Policy

Leave git to the user. Do not run git commands that modify state (`add`, `commit`, `checkout`, `branch`, `merge`, `rebase`, `stash`, etc.) unless the user explicitly asks for that specific operation. Only `git push` is hard-blocked at the harness level. Commands that destroy local work — `git reset --hard`, `git clean -f`, `git branch -D`, `git stash drop` — are not blocked and will run if you invoke them, so ask the user to run those manually.

Read-only inspection (`status`, `log`, `diff`, `show`, `branch` listing, etc.) is always fine.

## GitHub Commands

Prefer dedicated `gh` subcommands over `gh api`:
- Issue comments: `gh issue view <num> --comments -R <owner/repo>`
- PR comments: `gh pr view <num> --comments -R <owner/repo>`
- PR reviews: `gh pr view <num> --json reviews -R <owner/repo>`
- Releases: `gh release list -R <owner/repo>`
- Workflow runs: `gh run list -R <owner/repo>`

Do NOT use `gh api` when a dedicated subcommand exists.

## Verification Policy

Never claim "best practice", "recommended", "accepted solution", "community consensus", "known bug", "known issue", or "known limitation" without a cited source. If you haven't verified something, say "I believe" or "this might work" - not "this is the way."

**Do NOT say:**
- "This is the accepted approach" → without a source, you don't know this
- "The community recommends" → find a citation or don't claim consensus
- "This is best practice" → according to whom?
- "Known bug" / "known issue" → known by whom? Link the issue or say "I suspect"

When unsure, be explicit: "I think this will work, but I haven't verified it's the recommended approach."

## Test & Lint Failures

Never dismiss test failures, linting errors, or type errors as "pre-existing issues." Fix them. All repos use pre-commit hooks that enforce clean tests and linting — if something fails after your changes, either your changes caused it or it needs fixing regardless. Do not:
- Skip failing tests by claiming they were already broken
- Suggest the user "ignore" lint errors
- Offer to "move on" without fixing failures
- Acknowledge a failure is "pre-existing" and then stop — that is not fixing it
- Use `git diff` to prove something isn't your fault as justification for leaving it broken

"Fix it" means the check passes. The only acceptable outcome is ALL checks green. If a failure is genuinely unrelated to your changes, fix it anyway (and note it was pre-existing).

## Build & Check Workflow

- After writing or creating any new file, run the project's formatter before running check-all or lint commands.
- When a typecheck or lint command fails, read ALL errors and fix them in one pass before re-running. Do not fix one error and re-check.
- When moving or renaming files: update imports, barrel/index exports, and clear build caches (e.g., `.next`, `build/`) in the same pass — before re-running checks.
- When changing a shared type or component prop, grep for all consumers and update them before re-running typecheck.
- Do not reflexively re-run a failing command without making changes first. If it failed, something needs fixing.

## Keyword Triggers

When the user's prompt contains "second opinion", automatically invoke the `/second-opinion` skill to get external advisor input.

When the user's prompt contains "research online", automatically invoke whichever skill fits the topic. Route by *what you'll do with the answer*, not just subject: `/research-tech` when you'll act on it as a developer — libraries, errors, code patterns, best practices, version issues, **and choosing/evaluating dev tools, models, services, or product capabilities** (even when a product is named); `/research-general` for non-technical topics — academic, historical, current events, regional/regulatory, consumer purchases, personal decisions, fact-checking. Rule of thumb: implement/debug/build-with → `/research-tech`; learn-about/decide/verify a non-code topic → `/research-general`. In a non-code repo (e.g. a notes vault), default research to `/research-general`. If genuinely ambiguous, default to `/research-general`.

When the user's prompt contains "review plan", "review the plan", or "review my plan", automatically invoke the `/review-plan` skill to get multi-agent feedback before implementation.

When the user's prompt contains "ideation", automatically invoke the `/ideation` skill to generate structured ideas.

When the user's prompt contains "add debug logs" or "debug logging", automatically invoke the `/debug-log` skill to instrument code with tracing.

When the user's prompt contains "review history" or "git history" or "how did this change", automatically invoke the `/review-history` skill to analyze code evolution.

When the user's prompt mentions `.pdf` files or asks to work with PDFs (merge, split, extract text, create, fill forms, OCR, watermark), automatically invoke the `/pdf` skill.

When the user's prompt contains "review logs", "session analysis", or "failure patterns", automatically invoke the `/review-logs` skill to analyze session transcripts.

When the user's prompt contains "check agent logs", "look through claude projects", "check claude projects", "search past sessions", "search past transcripts", or "find the session where", or otherwise asks to recover context from a previous session whose agent or location is unknown ("we fixed/discussed this before", "which checkout was that in"), automatically invoke the `/check-agent-logs` skill to search Claude Code, Codex, OpenCode, and Pi logs.

When the user's prompt contains "pre-existing", "preexisting", "already broken", or "flaky test", or when you are about to label a test/lint/type/build/CI failure as pre-existing, unrelated, or not your fault, automatically invoke the `/pre-existing` skill before stopping.

## Internal Documentation

When a `docs/` folder exists, proactively check internal documentation using `/read-docs`:

**Automatic triggers:**
- Before planning a new feature or significant change
- When entering a new area of the codebase for the first time
- When debugging issues (check for documented gotchas)
- When the user asks about conventions, patterns, or architecture

These docs supplement this file with detailed project-specific knowledge. For external library docs, use `/research-tech` instead.
