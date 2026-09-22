# Write targets

Every place in this repo that pins an OpenRouter model id. All six must move
together or the trio drifts apart.

Ids are always OpenRouter ids (`vendor/model`), because every one of these
paths bills through OpenRouter. `rank_models.py` prints the exact id — never
hand-guess one. `deepseek/deepseek-v4-pro` is the **0423** build;
`deepseek/deepseek-v4-pro-0813` is the newer one. Names collide; ids do not.

## Default tier bindings

Proposed on each run, confirmed by the user before anything is written.

**The default binds to the cheapest tier that can carry everyday work.** Which
tier that is comes out of the ranking, not out of this table — the run decides it
and says so. An unattended default is what quietly drains the OpenRouter balance,
so it has to be the cheapest option that can actually do the job.

**"Cheapest" is not always the low tier.** `$/task` is a benchmark blend; a very
cheap model can win low on terseness while costing *more per input token* than the
tier above it. When low is also a real capability drop, mid is the correct default
and low keeps only the terse one-shot slots (`occli`, the haiku rung). Whichever
tier wins, everything above it must be reached deliberately: `clor`'s opus alias
and `ocs`.

**This cycle:** low = GPT-6 Luna, mid = MiMo-V2.6-Pro, high-main = GPT-6 Sol
(max, user-selected past the cost cliff), high-fallback = Muse Spark 1.3 (max) —
and **mid holds the default**. Luna is cheaper per session but 9 index points
weaker; MiMo's $0.0036/M cache reads keep a typical session under the previous
default's cost.

**User-selected advisors:** Pi uses GLM-5.3 at `max`; OpenCode uses Kimi K3 at
`max`. OpenCode's advisor selection overrides its high-fallback tier binding.

| # | File | Key | Binding |
|---|------|-----|------|
| 1 | `loadout/settings/pi.json` | `defaultModel` | **default** |
| 1 | `loadout/settings/pi.json` | `defaultThinkingLevel` | default tier's effort |
| 1 | `loadout/settings/pi.json` | `enabledModels` | all four |
| 2 | `loadout/settings/opencode.json` | `model` | **default** |
| 2 | `loadout/settings/opencode.json` | `provider.openrouter.models` | all four |
| 3 | `.airc.d/claude.zsh` | `clor` → `CLOR_MODEL` start alias | the alias holding the default |
| 3 | `.airc.d/claude.zsh` | `clor` → `ANTHROPIC_DEFAULT_HAIKU_MODEL` | low |
| 3 | `.airc.d/claude.zsh` | `clor` → `ANTHROPIC_DEFAULT_SONNET_MODEL` | mid |
| 3 | `.airc.d/claude.zsh` | `clor` → `ANTHROPIC_DEFAULT_OPUS_MODEL` | high-main |
| 3 | `.airc.d/claude.zsh` | `clor` → `CLAUDE_CODE_SUBAGENT_MODEL` | **default** |
| 4 | `.airc.d/opencode.zsh` | `ocs` alias | high-fallback |
| 5 | `pratfall/config.toml` | `cmdgen-opencode` → `model` | low |
| 6 | `pratfall/config.toml` | `advisor-pi` → `model` | high-main |
| 6 | `pratfall/config.toml` | `advisor-pi` → `effort` | max |
| 6 | `pratfall/config.toml` | `advisor-opencode` → `model` | Kimi K3 (user override) |
| 6 | `pratfall/config.toml` | `advisor-opencode` → `effort` | max |

Subagents take the **default**, not low: they run long-context exploration, which
is exactly where a terse-but-pricier low tier loses on both capability and cost.

### Not targets

- `loadout/settings/claude.json` — its `model` / `effortLevel` drive real
  Anthropic models on the subscription. The trio is OpenRouter-only.
- `bin/jina-fetch` — pins `DEFAULT_MODEL` and `FALLBACK_MODEL`, both OpenRouter,
  but they are page-extraction models chosen by a separate harness
  (`benchmark/bench-models.py`, written up in `benchmark/extract-model.md`) on
  criteria this ranking does not measure: extraction latency, faithfulness to the
  page, and provider count as 429 insurance. Intelligence index is irrelevant to that
  job. Leave both alone and re-run that benchmark instead.

---

## 1. `loadout/settings/pi.json`

This is the loadout **base document** — an input, never generated. The generated
file is `~/.pi/agent/settings.json`, composed from this base plus the `plugins`
slice (which supplies `packages`).

```json
"defaultProvider": "openrouter",
"defaultModel": "<low id>",
"defaultThinkingLevel": "<low effort>",
"enabledModels": [
  "openai-codex/gpt-6-astra",
  "openai-codex/gpt-6-luna",
  "openai-codex/gpt-5.6-terra",
  "openai-codex/gpt-6-sol",
  "openrouter/<low id>",
  "openrouter/<mid id>",
  "openrouter/<high-main id>",
  "openrouter/<high-fallback id>"
]
```

- `enabledModels` entries carry an `openrouter/` prefix; `defaultModel` does not.
- Leave the `openai-codex/*` entries alone — that ladder is not OpenRouter and
  is not part of the trio.
- **Run `loadout sync --global` after editing** or the change never reaches Pi.
- Pi writes `/model` and `/settings` picks into the *generated* file, where the
  next sync discards them. A pick worth keeping has to be copied into this base.
- Pi caches its resolved model list in `~/.pi/agent/mcp-cache.json`-style state
  and its catalog in `~/.pi/agent/models-store.json`. A model too new for the
  catalog still works but warns `Model "…" not found for provider "openrouter".
  Using custom model id.` Run `pi update` to refresh the catalog; never hand-edit
  `models-store.json`.

## 2. `loadout/settings/opencode.json`

This is the loadout **base document** — an input, never generated. The generated
file is `~/.config/opencode/opencode.json`.

```json
"model": "openrouter/<low id>",
"provider": { "openrouter": { "models": {
  "<low id>": {}, "<mid id>": {},
  "<high-main id>": {}, "<high-fallback id>": {}
} } }
```

- `model` takes the `openrouter/` prefix; the `models` map keys do not.
- **Run `loadout sync --global` after editing** or the change never reaches
  OpenCode. Use `claude-raw`/an unsandboxed shell — sync writes outside `~/wrksp`.
- `mcp/sync.py` co-owns the destination's `mcp` key. Run `mcp/sync.py` before
  `loadout` if both need syncing; loadout preserves `mcp` but only reads what is
  currently on disk.
- Per-model reasoning effort: the schema exposes a free-form `options` object per
  model (provider passthrough, so `{"reasoning": {"effort": "high"}}` is the
  shape OpenRouter takes) and a `variants` key. Neither is verified here — leave
  the maps as `{}` unless you have tested the behaviour, and say so rather than
  claiming effort is configured.

## 3. `.airc.d/claude.zsh` — the `clor` function

Runs Claude Code against OpenRouter. **No Anthropic model is involved.**
`ANTHROPIC_DEFAULT_*_MODEL` overrides what each slot *resolves to*, so
`haiku`/`sonnet`/`opus` survive only as the labels on Claude Code's model
switcher — `/model sonnet` in a `clor` session runs the mid-tier OpenRouter
model. The three slots are remapped cheap→strong so the switcher becomes a
low/mid/high control.

```zsh
local start="${CLOR_MODEL:-<alias holding the default tier>}"
…
ANTHROPIC_DEFAULT_HAIKU_MODEL='<low id>[1m]'
ANTHROPIC_DEFAULT_SONNET_MODEL='<mid id>[1m]'
ANTHROPIC_DEFAULT_OPUS_MODEL='<high-main id>[1m]'
CLAUDE_CODE_SUBAGENT_MODEL='<default tier id>[1m]'
```

- **`start` is a fifth edit, and it is easy to miss.** The three `ANTHROPIC_*`
  slots only decide what each alias *resolves to*; `start` decides which alias a
  `clor` session opens on. Point it at whichever alias carries the default tier —
  `sonnet` when mid is the default, `haiku` when low is. Leaving it on `haiku`
  while the default moved to mid silently opens every session on the weak tier.

- **Keep the `[1m]` suffix.** It declares the 1M context window to Claude Code.
  Only append it to a model whose `context` column in the ranking is ≥ 1000k;
  for a smaller-context model drop the suffix rather than lying about the window.
- Keep the backslash line continuations and the single quotes intact — the whole
  block is one `sops exec-env` argument string.
- `CLOR_MODEL` / `CLOR_EFFORT` still override the starting tier and effort at
  call time; do not hardcode those.

## 4. `.airc.d/opencode.zsh` — the `ocs` alias

```zsh
alias ocs="opencode -m openrouter/<high-fallback id>"
```

`ocs` exists to reach *past* the configured default, so it has to stay strictly
above whichever tier holds it. It tracks high-fallback however the default moves,
which is why it is pinned to a named tier rather than to "one above the default".

## 5. `pratfall/config.toml` — the `cmdgen-opencode` profile

One-shot shell-command generation, behind the `occli` alias in
`.airc.d/llmcli.zsh`:

```toml
[profiles.cmdgen-opencode]
model = "openrouter/<low id>"
```

Cheap and latency-sensitive — this slot wants the low tier regardless of what
the interactive defaults do.

Its two siblings are **not** targets. `cmdgen-claude` pins `haiku` on the
subscription, and `cmdgen-codex` pins a Codex-ladder model; neither is
OpenRouter, which is all this ranking covers. `cmdgen-codex` additionally cannot
take a `-mini`: Codex on a ChatGPT account rejects those with a 400.

## 6. `pratfall/config.toml` — the `advisor-pi` and `advisor-opencode` profiles

The `/second-opinion` advisors. Default bindings follow high-main for Pi and
high-fallback for OpenCode. Preserve the user-selected advisor overrides above
when proposing tier updates; include both advisor models and reasoning levels in
the proposal for approval.

Both take prat's normalized `effort`, which renders as Pi's `--thinking` and
OpenCode's `--variant`. Verify the selected OpenCode model exposes a `max`
variant with `opencode models openrouter --verbose`. These settings apply to
every consultation, including `--quick`.

`loadout/skills/second-opinion/SKILL.md` no longer names a model — it invokes
these profiles — so it needs no edit and no `loadout sync`. The file is
symlinked to `~/.config/pratfall/config.toml`, so a change takes effect at once.

`publish/overrides/second-opinion/SKILL.md` is the public variant and **is** a
target: it calls the CLIs directly and carries its own copies of both model ids
and reasoning flags. Update it in the same pass, or the published skill drifts.

## After writing

1. `loadout sync --global` — required for targets 1, 2 and 6. Needs an
   unsandboxed shell (`claude-raw`), since it writes outside `~/wrksp`.
2. `source ~/.airc` — reloads targets 3–5 in the current shell. Idempotent.
3. `loadout check --global` — must be clean; the lefthook pre-commit hook runs it.
