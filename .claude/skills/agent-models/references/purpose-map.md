# Purpose map

Every place a model is chosen on this machine, grouped by what it is used for.
Answer "what runs where" questions with this map, open every proposal with it,
and end every apply with it. Read each value from its source at the time of
answering — never from this file's examples or from memory.

## Output format

One table per group, in this order, with these columns:

| Purpose | Command / profile | Model | Effort | Billing | Source |

- **Model** is the exact id the harness receives. Write an inherited value as
  `→ <resolved id>` and say what it inherits from (for example, `advisor-codex` has
  no `model` key, so it runs Codex's startup default).
- **Effort** is the configured level, `—` when the harness takes none, or
  `harness default` when nothing in this repo sets it. Never guess a harness's own
  default.
- **Billing**: Claude subscription, ChatGPT subscription, OpenRouter, OpenCode Go,
  Vercel Token Pass, Anthropic API credits, or Factory.
- In a proposal, replace **Model** and **Effort** with `current → proposed`, write
  `unchanged` where nothing moves, and list the rows a pick would change before the
  per-selection detail tables.
- Flag uncommitted edits to any source with `git status --short`, and say so when
  the map reflects the working tree rather than `HEAD`.

## Groups and sources

### 1. Interactive sessions (what starts with no tier argument)

| Command | Source |
|---|---|
| `claude` | `loadout/settings/claude.json`: `model` alias, `effortLevel`, per-model `modelSettings` |
| `codex` | `loadout/defaults/codex.json`: `model`, `model_reasoning_effort` |
| `pi` | `loadout/settings/pi.json`: `defaultProvider`, `defaultModel`, `defaultThinkingLevel` |
| `pix` | `.airc.d/pi.zsh`: the `preset=` fallback in `pix()` |
| `picc` | `.airc.d/pi.zsh`: `--model` in `picc()` |
| `opencode` / `oc` | `loadout/settings/opencode.json`: `model` |
| `ocs` | `.airc.d/opencode.zsh`: the `ocs` alias |
| `droid` | `loadout/settings/droid.json`: `sessionDefaultSettings.model` |
| `clor` | `.airc.d/claude.zsh`: `CLOR_MODEL:-` start alias resolved through its `ANTHROPIC_DEFAULT_*_MODEL` slot, `CLOR_EFFORT:-` |

### 2. Session tiers

`claude <tier>`, `codex <tier>`, `pix <tier>` from `.airc.d/07-model-tiers.zsh`. One
row per tier per lab; note that `codex` and `pix` share the `openai` table.

### 3. Switchers inside a session

`clor`'s `/model haiku|sonnet|opus` slots in `.airc.d/claude.zsh`. List pi's
`enabledModels` and droid's `modelFavorites` in one line each: they are picker
entries, not defaults.

### 4. Sub-agents

| Harness | Source |
|---|---|
| Claude (subscription) | `loadout/settings/claude.json` `env.CLAUDE_CODE_SUBAGENT_MODEL`; absent means each spawn chooses or inherits |
| Codex | `loadout/instructions/codex-subagent-models.md` table |
| `clor` | `CLAUDE_CODE_SUBAGENT_MODEL` in `.airc.d/claude.zsh` |
| OpenCode | the session model, unless an agent in `opencode.json` sets `model` |

### 5. `/second-opinion` advisors

`pratfall/config.toml` `[profiles.advisor-*]`: `model`, `effort`. A profile without
`model` inherits that CLI's group-1 default; resolve it. Show
`publish/overrides/second-opinion/SKILL.md` as a separate line when it differs, since
the public skill carries its own ids.

### 6. One-shot shell commands

`ccli`, `cxcli`, `occli` → `pratfall/config.toml` `[profiles.cmdgen-claude|codex|opencode]`.
`cmdgen-claude`'s `haiku` alias resolves on the Claude subscription.

### 7. Page and file extraction

`jina-fetch` and `distill` → `DEFAULT_MODEL` / `FALLBACK_MODEL` in `bin/extraction.py`;
the pi dev-phase classifier → `MODELS` in `mods/dev-phase/pi/extension.ts`. Note when
the two disagree.

Cursor (`agent` / `cursor-agent`) is outside this skill; omit it.
