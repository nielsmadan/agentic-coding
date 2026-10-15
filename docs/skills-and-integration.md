# Skills and harness integration

Global skills live in `loadout/skills/<name>/`; every harness surfaces the
available ones with their descriptions, so this file does not restate them. The
human-facing catalog (arguments, examples) is
[`loadout/skills/README.md`](../loadout/skills/README.md).

loadout renders each skill to all four harnesses — `~/.claude/skills/`,
`~/.codex/skills/`, `~/.config/opencode/skills/` and `~/.pi/agent/skills/`. Those
are generated directories: edit the source, never the output.

What follows is the part that is *not* discoverable from the skill list itself.

### Extending code-review per language / per project

`code-review` first runs `review-tidy --fix` as an unscored cleanup preflight. `review-tidy` invokes `review-comments --fix`, applies mechanical fixes, and runs formatting last. All three skills remain separately callable. The review then layers four tiers of checks:

1. **9 language-agnostic aspects** — the default comprehensive set (correctness, architecture, security, …); explicit aspect flags select a subset. Correctness combines logic and defensive checks; `--logic` and `--defensive` alias `--correctness` and select one reviewer.
2. **Language reviews** — global skills named `review-<language>` in `loadout/skills/`. Auto-invoked when `code-review` detects that language in the scoped files. Add a new language by creating `review-<language>/SKILL.md` and adding a row to the detection registry in `code-review`'s Step 3b.5.
3. **Project review** — an *individual project* can define `.claude/skills/review-project/SKILL.md` for checks unique to that codebase. `code-review` calls it only when it exists; projects without one are unaffected. The minimal shape is documented in `code-review`'s "Language & project reviews" section.
4. **Library-use review** — global `review-library-use` checks code against a per-repo `library-use` reference (docs-derived, version-specific correct-usage conventions). Auto-invoked when the repo has `.claude/skills/library-use/SKILL.md`, which the global `library-docs` skill generates and refreshes. Trio: `library-docs` (build/refresh) → `library-use` (per-repo reference) → `review-library-use` (audit).

### Adding a skill

Drop the skill at `loadout/skills/<name>/SKILL.md` and run `loadout sync --global`.
The directory *is* the declaration — there is no list to add it to, and it reaches
all four harnesses.

One optional hookup: add an entry to
[`loadout/skills/README.md`](../loadout/skills/README.md) (the human-facing catalog —
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

Unmarked skills pass through untouched, so the mechanism costs nothing until used. `loadout check --global` reports any drift, and `loadout sync` refuses
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
  models and writes them into every file that pins a model id (`loadout/settings/pi.json`,
  `loadout/settings/opencode.json`, `clor` in `.airc.d/claude.zsh`, the `ocs`
  alias, the `occli` backend, and the two `second-opinion` advisors). Ranks
  candidates from Artificial Analysis by Intelligence Index vs cost per task (the
  Agentic Index it used to rank on vanished from AA in September 2026); never
  picks Grok, and prefers non-frontier-lab models on a tie.

  Artificial Analysis pages are JS-rendered — fetchers return prose with no
  numbers. `scripts/rank_models.py` parses the per-model datasets out of the RSC
  payload (`self.__next_f`) that `/leaderboards/models` and `/models` server-render,
  joins them on `slug`, then resolves exact
  OpenRouter ids from `openrouter.ai/api/v1/models`. Model *names* collide across
  builds (`deepseek/deepseek-v4-pro` is the 0423 build, not the 0813 one), so ids
  always come from that API, never from a name.

## Permissions

Shell-command and MCP permissions for all four agents (Claude, Codex, OpenCode, Pi) are generated from a single source of truth: **`loadout/permissions.toml`**. The renderers live in **`loadout`** (a separate tool, installed on `PATH`); `loadout.toml` declares which file each one writes.

**Never hand-edit a generated file** — a lefthook pre-commit hook (`loadout check --global`) rejects any drift. `loadout.toml` names the slices, not the destinations — those come from loadout's agent preset, so `loadout explain <fragment>` or `loadout check --global` is what tells you where something lands. Nearly all of them are now written **straight to the machine path the agent reads** and are not staged in this repo at all — `~/.claude/settings.json`, `~/.codex/rules/permissions.rules`, `~/.codex/config.toml` and the rest. One exception lands here: `loadout/defaults/codex.owned`, the record of which keys loadout manages in `config.toml` rather than a config file itself.

**Some outputs are only half generated.** Where a file also holds hand-maintained settings, that half lives in a **base document** which is an input and is never written:

| edit this | to change | which is generated into |
|---|---|---|
| `loadout/permissions.toml` | any shell or MCP rule, on every agent | all seven permission files |
| `loadout/settings/claude.json` | hooks, statusLine, model, env, `permissions.defaultMode` — for **both** profiles | `~/.claude/settings.json` |
| `loadout/settings/claude-afk.json` | the default profile's `env.CLAUDE_AFK_TIMEOUT_MS` only | `~/.claude/settings.json` under the default profile |
| `loadout/settings/opencode.json` | `model`, `provider`, `$schema` | `~/.config/opencode/opencode.json` |

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
- `~/.pi/agent/mcp.json` (`mcpServers`, read by Pi's native MCP support)

A `transport = "http"` entry takes `url` plus an optional `auth_env_var`; `transport = "stdio"` takes `command`, optional `args`, and an optional `[<name>.env]` table. **Only ever record the env var's NAME** — each harness has its own interpolation syntax (`${VAR}` for Claude and Pi, `{env:VAR}` for OpenCode, `bearer_token_env_var` for Codex), and loadout refuses a server whose keys it does not recognise rather than silently rendering one that connects unauthenticated.

Pi's native MCP uses Authorization headers. `loadout.toml` disables the adapter-oriented Pi
MCP preset and selects `claude-project-servers` for Pi's destination, which emits the compatible
standard format. This keeps server definitions shared without changing other harnesses.

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

**Nothing reserializes `~/.codex/config.toml`, and that is the design.** Loadout's surgery works
line-wise, using `tomllib` only to validate the result. The
comments, the nono block and the project tables survive because no code path touches those bytes,
not because a writer preserved them. Do not "improve" this into a parse-mutate-serialize round
trip: that trades untouched for preserved-if-the-library-is-careful, and adds a dependency to a
script `install.sh` runs on a fresh machine.

**loadout evicts nono's `developer_instructions` itself.** Everything the old
`sync_config.py` merged — `[mcp_servers.*]`, `[plugins.*]`, `[marketplaces.*]`, the model
defaults — is loadout's, and so is this: `loadout/defaults/codex.json` lists the key under
`$remove`, which owns it in order to delete it. The guidance it used to hold moved to
`loadout/instructions/sandbox.md`, where all four harnesses get it rather than Codex alone.
`nono update` puts the block back; the next `loadout sync` strips it, body and all.

Deleting rather than replacing is the choice that matters: one document to maintain instead of
two, and no contest over who writes the key last.

**`publish/` generates the public skills collection.** `publish/sync.py` renders the
`publish`-classified skills from `loadout/skills/`, preferring complete skill
directories in `publish/overrides/<name>/` when present, into
[nielsmadan/skills](https://github.com/nielsmadan/skills) — a Claude Code plugin
marketplace and `npx skills` collection; a workflow in that repo runs it hourly.
`publish/skills.toml` classifies every skill into a README group under `[groups]` (published), into `private` (in the repo but unpublished), or into `local` (gitignored — never pushed, this repo being public), fail-closed:
the pre-commit hook runs `--check-manifest --check-sources` on every commit, so an
unclassified skill or a personal string (`~/ac`, `/Users/nielsmadan`, …) in a
publishable source rejects the commit — even one that seems unrelated. Run it as a
script path (`python3 publish/sync.py`), never `python3 -m publish.sync`: `-m` puts
the repo root on `sys.path`, where the `loadout/` config directory shadows the
installed `loadout` package. The `loadout` package is a `uv tool` install, not
importable from system Python — only `--out` (render) needs it; the checks and the
tests (`python3 -m unittest publish.test_sync`) run without it. Source checks scan
the selected public variant. Overrides must name a published skill and contain
`SKILL.md`; invalid overrides fail rather than falling back. Supporting files come
entirely from the selected directory. See
[`publish/overrides/README.md`](../publish/overrides/README.md) for the workflow.

**Codex validates none of this.** `model_reasoning_effort = "bogus"` is accepted silently and
reported as the session's effort; a wrong value fails server-side at first use. The published
[config reference](https://learn.chatgpt.com/docs/config-file/config-reference) also lags the
binary — it lists `minimal | low | medium | high | xhigh`, while codex-cli 0.149.1 carries `max`
and `ultra` as well. Verify a new value by running `codex exec` once and reading the effort it
reports back.

The loadout side is pinned by `test_a_removed_key_is_stripped_from_the_destination` and
friends; `$remove` is documented in loadout's README.

## Pratfall

[pratfall](https://github.com/nielsmadan/pratfall) (`prat`) runs one-shot agent
CLIs behind short aliases and named profiles. Two things here use it:
`/second-opinion` and the `ccli` / `cxcli` / `occli` command generators in
`.airc.d/llmcli.zsh`. Both name a profile from `pratfall/config.toml`
(`advisor-*` and `cmdgen-*`) rather than spelling out per-CLI flags.

**The point is that the guards live in the profile, not in the caller.** prat
does **not** sandbox Codex for you — `prat cx` renders a plain `codex exec` with
no `--sandbox`. `/second-opinion`'s read-only guarantee is `native_args` and
`tools` on `advisor-claude` and `advisor-pi`, which is exactly why the skill must
never fall back to a bare `prat cx`.

**`advisor-codex` runs with `--sandbox danger-full-access`, on purpose.** Codex
reads files through shell commands, and both `read-only` and the base config's
`workspace-write` wrap each command in Codex's own Seatbelt sandbox, which nono
refuses to start inside a sandboxed session — so every command, `cat` included,
failed and Codex answered without reading anything. `/second-opinion` only runs
from nono sessions, so nono is Codex's boundary there. In an unsandboxed session
this profile can write anywhere; do not run the skill from one. Measured with a
planted-word repo: every advisor, called from each of the four sandbox profiles,
read the files and left the repo unchanged.

**prat reserves some native flags.** Passing one after `--` is refused with
`this option is controlled by prat`. Measured: claude's
`--no-session-persistence`. Claude's `--system-prompt` and
`--disable-slash-commands`, codex's `--sandbox`, `--skip-git-repo-check`,
`--disable` and `--profile`, pi's `--no-session` and opencode's `--agent` all
pass through.

**Codex's `-c` / `--config` is reserved per key, not as an option** — as of prat
0.9.1, which is therefore the floor for `pratfall/config.toml`. prat sets
`developer_instructions`, `model_reasoning_effort`, `service_tier` and `model`,
and rejects an override of one of those (or a dotted descendant) only while the
public option that sets it is active; every other key passes through. So
`advisor-codex` carries `-c agents.enabled=false` directly. That guard is not
redundant with the two `--disable` flags, which set `features.<name>`: the base
`~/.codex/config.toml` sets `[agents] max_concurrent_threads_per_session = 16`.

Before 0.9.1 the whole option was reserved and the key had to travel in a Codex
config profile instead. That is gone, and good riddance — Codex accepts an
unknown `--profile` name silently, so a typo failed *open* and dropped the guard
with no error, whereas a bad `-c` key now fails loudly at `prat config validate`.

**prat has no `env` field in profiles.** OpenCode's per-run task denial
(`OPENCODE_CONFIG_CONTENT=…`) therefore stays inline in the caller.

**prat execs the real binary off PATH**, so it bypasses the `claude` / `codex` /
`pi` / `opencode` zsh wrappers in `.airc.d/05-sandbox.zsh` — no nono, no
sops-exec. Inside an agent session that is right, and it is what the old
`command codex exec` prefix did by hand; nesting nono would hit
`forbidden-sandbox-reinit`. In an *interactive* shell it is not, which is why
`llmcli.zsh` calls `sops-exec prat …`: `occli` needs `OPENROUTER_API_KEY`. Those
three run unsandboxed as a result, so their profiles disable tools where the
backend supports it. For the same reason, do **not** point
`[agents.NAME].command` at a sandbox wrapper — that config is global and would
nest nono for every caller, agent sessions included.

**Codex on a ChatGPT account rejects the mini models.** Both `gpt-5.4-mini` and
`gpt-5.4-codex-mini` return `400 … not supported when using Codex with a ChatGPT
account`; `cmdgen-codex` pins `gpt-5.6-luna` instead.

Model ids in these profiles are targets of the `agent-models` skill — see
`.claude/skills/agent-models/references/targets.md`, entries 5 and 6.

**Permissions need no entry.** `loadout/permissions.toml` has `[shell] default =
"allow"` with an empty `allow` list, so `prat` runs unprompted on all four
agents.

**`/second-opinion` has a public variant that does not use prat.** The published
collection cannot assume `prat` is installed, so
`publish/overrides/second-opinion/` carries a copy that calls the CLIs directly.
The two must be fixed together — see Public skill variants in
[`publish/overrides/README.md`](../publish/overrides/README.md).

## Local Claude Plugins

A plugin developed locally (`mouthfeel`, at `~/wrksp/all/mouthfeel`) is wired up in **two halves with two owners**, and they must agree:

- **Enablement** — `loadout/plugins/claude.json`, rendered into the generated `~/.claude/settings.json`. Without an entry there, `claude plugin enable` writes the key at runtime and the next `loadout sync` discards it, silently disabling the plugin. `loadout/plugins/unsandboxed.json` sets it to `null`, which is how that profile drops the plugin.
- **Marketplace registration** — `sync.sh`'s `sync_claude_plugins`, driven by the `LOCAL_MARKETPLACES` array, which names the *built* plugin directory rather than the repo root. A stale entry there fails silently: the registration step simply finds nothing to register. `~/.claude/plugins/known_marketplaces.json` is an install registry Claude rewrites itself (install paths, timestamps), so loadout deliberately does not render it — the same constraint as `.claude.json` for MCP servers. Add-only: if the built path moves, `claude plugin marketplace remove <name>` and re-run.

**`enabledPlugins` used to live in the settings base, and must not go back there.** The plugins slice assigns the key unconditionally, and composition is residual-first — so with `plugins = ["claude"]` declared in `loadout.toml`, a copy left in `loadout/settings/claude.json` is overwritten with no message.

Reload after a source change is `npm run dev:claude` in the plugin repo: it stamps a fresh version into `dist/claude/mouthfeel/.claude-plugin/plugin.json`, then runs `claude plugin update` and `claude plugin enable`. The version stamp is what stops Claude serving the cached copy. Nothing sandbox-specific is needed — `~/wrksp` and `~/.claude/plugins` are both granted.

**Mods** (`mods/<name>/`, a hooks module with no marketplace or version) take neither half. `sync.sh`'s `sync_claude_mods` copies each to `~/.claude/mods/<name>`, and `CLAUDE_CODE_PLUGIN_DIRS` in `loadout/settings/claude.json` loads that copy in every Claude session (several paths are separated by `:`). Sessions watch the copy, not the repo, so an edit reaches them on the next `./sync.sh` rather than on save; to try one first, `claude --plugin-dir mods/<name>` hot-reloads from the working copy. Claude Code writes its type declarations into `.claude-plugin/types/` of the folder it loads (gitignored here), and `sync_claude_mods` copies the loaded copy's back, so `tsc -p mods/<name>` works once any interactive session has loaded the mod. `claude plugin test mods/<name>` needs no declarations.

## Hooks

Hook **scripts** live in `loadout/module-config/claude/hooks/`; their **wiring** is a separate slice, `loadout/hooks/claude.json`. Neither belongs in `~/.claude/settings.json`, which is generated in full and will discard the edit at the next `loadout sync`. When adding one:

- **Make it executable (`chmod 755`).** A non-executable hook is silently skipped — the event fires as if no hook existed. Git preserves mode `100755` once set.
- **Both profiles get it automatically.** `loadout.toml` gives Claude `hooks = ["claude", "hooklinesinker-claude"]` under either profile, so a hook added to the wiring reaches both. The settings overlay that does differ is `claude-afk`, and it carries only `env.CLAUDE_AFK_TIMEOUT_MS`. Run `loadout sync` afterwards.
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
