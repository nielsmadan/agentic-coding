---
name: agent-models
description: Pick and apply the low / mid / high-main / high-fallback OpenRouter coding models for pi, OpenCode, the clor Claude-Code-on-OpenRouter wrapper, and the second-opinion advisors. Ranks candidates from Artificial Analysis by agentic index vs cost per task, resolves exact OpenRouter ids, and updates every config that pins one. Use when the user says "pick models", "update the models", "refresh the model tiers", "which models should the agents use", "set the coding models", "new model came out", or asks what pi/opencode/clor are currently running.
---

# Agent Models

Chooses four OpenRouter models — **low**, **mid**, **high-main**,
**high-fallback** — and writes them into the six places this repo pins a model id.

Standing constraints, not preferences:

- **Never pick a Grok / xAI model.** `rank_models.py` filters them out entirely.
- **Prefer alternative labs.** OpenAI, Anthropic and Google are eligible but only
  win a tier when clearly ahead of the best alternative; the point of these
  harnesses is to get a read on non-frontier-lab models.
- **Rank on agentic index vs cost per task**, the two axes of the chart at
  `artificialanalysis.ai/models?intelligence=agentic-index`.

## Instructions

### Step 1: Rank the candidates

```bash
python3 .claude/skills/agent-models/scripts/rank_models.py
```

It fetches the Artificial Analysis models page, parses the full per-model
dataset out of the RSC payload the page server-renders, resolves each model to
an exact OpenRouter id, and prints a table plus the cost/agentic Pareto frontier.
Add `--no-cache` to bypass the 6h fetch cache, `--all` to show excluded models,
`--json` for machine-readable output.

Do **not** read the chart through a fetcher instead. The page is JS-rendered:
`WebFetch` and `jina-fetch` both return prose with no numbers in it.

Read the `Frontier` and `Cost cliffs` sections — that is where the tiers are.

### Step 2: Choose four models

Work off the frontier, cheapest first. Marginal cost per agentic point is the
signal: a segment that buys many points cheaply is inside a tier, a segment that
buys almost nothing for a lot of money is the cliff between tiers.

| Tier | Rule |
|------|------|
| **low** | Cheapest frontier point worth running at all. Its natural home is the terse one-shot slots (`occli`, the haiku rung) — it only earns the default as well if it is *also* cheapest per input token. |
| **mid** | The next frontier point up. Usually the best value on the board, and usually the right default. |
| **high-main** | Highest agentic index *before* the first cost cliff. Buying past a cliff is the mistake this ranking exists to prevent. |
| **high-fallback** | Best model from a **different creator** at comparable capability — within ~6 agentic points of high-main, at similar cost. A second opinion from the same lab is not a second opinion. |

**Prefer the frontier points themselves.** When the frontier has three points
below the cliff, that *is* the ladder — take them in order rather than reaching
off-frontier to fill a tier. A tier filled with a dominated model is worse than a
tier that repeats the one above it.

Apply the alternative-lab tiebreak: when a big-lab model and an alternative are
close in a tier, take the alternative. Take the big-lab model only when it is
clearly ahead at comparable-or-lower cost — "clearly ahead" means ahead on the
ranking axes, not ahead on one axis while behind on the others.

Note each pick's **effort** column (`max`, `xhigh`, `high`). The benchmark number
is for that effort level, so the effort has to carry into the config — a model
recorded at `max` and run at `low` is not the model that was measured.

### Sanity-check the ladder before presenting it

Four checks. Each one has caught a real bad pick; run all four.

1. **Cost must not invert.** low ≤ mid ≤ high-main on `$/task`. A mid that costs
   more than high-main is not a step up, it is a dominated pick — re-pick it, or
   collapse the tier into high-main and say so.
2. **No dominated pick wins a tier.** If a candidate is behind another on *both*
   agentic index and cost, it cannot take a tier on intelligence index alone.
   (This is exactly how GPT-5.6 Sol nearly took mid at $0.953 while GLM-5.3 sat
   above it on agentic *and* below it on price.)
3. **Check input price and tokens/task, not just `$/task`.** `$/task` is a
   benchmark blend. Real agentic sessions re-send their whole context every turn,
   so the bill tracks `price_in` far more closely than `$/task` — a terse model
   can win `$/task` and still be the more expensive one to actually run.
4. **Name which tier holds the default, out loud.** It is whichever tier is
   cheapest per input token among those that can carry everyday work — not
   automatically low. See `references/targets.md`.

### Getting tokens per task

The printed table has no token columns, and `--json` does not carry them either.
They are on the raw AA record, so pull them with the script's own parser:

```python
import importlib.util
spec = importlib.util.spec_from_file_location("rm", ".claude/skills/agent-models/scripts/rank_models.py")
rm = importlib.util.module_from_spec(spec); spec.loader.exec_module(rm)
for r in rm.aa_models():
    otp = r.get("intelligenceIndexOutputTokensPerTask") or {}   # reasoning / answer / output
    can = r.get("canonicalIntelligenceIndexTokenCount") or {}   # suite totals, for the in:out ratio
    # input tokens per task = otp["output"] * can["input"] / can["output"]
```

`otp["output"]` checks out exactly against `cost.output ÷ price_out`, so the
derivation is sound. Use it whenever a tier decision turns on verbosity.

### Pricing a real workload

To compare candidates on how *this machine* actually bills rather than on the
benchmark blend, replay a measured session's token split at each model's prices.
`rl usage session <id>` gives the split; cache reads bill at roughly 12% of the
input rate (measured on OpenRouter, muse-spark: $0.15/M read vs $1.25/M input):

```
cost ≈ input_M × price_in  +  cache_read_M × 0.12 × price_in  +  output_M × price_out
```

Validate it against the session's own recorded cost before trusting it — pi
records per-turn `usage.cost`, so the replay can be checked to the cent.

### Step 3: Present the proposal, and stop

Show a table: tier, model name, creator, agentic index, cost per task, effort,
and exact OpenRouter id. Say in one line per tier why it won, and name the
runner-up so an override is a one-word reply.

Call out anything surprising — a tier that did not move, a pick that is off the
frontier, a cliff that shifted, a current model that has dropped out of the
ranking entirely.

Then show the binding table from `references/targets.md` and **wait for
confirmation**. Do not write any file before the user approves the four picks
*and* the bindings.

### Step 4: Apply

Read `references/targets.md` and make all six edits. It carries the exact key
names, prefix rules (`openrouter/` on some keys, not others), the `[1m]` context
suffix on `clor`, and which files are loadout sources vs generated.

Preserve unrelated content in every file: pi's `openai-codex/*` entries, the
`clor` continuation backslashes, `CLOR_MODEL` / `CLOR_EFFORT` overrides.

### Step 5: Sync and verify

```bash
loadout sync --global     # required for opencode + second-opinion; needs an unsandboxed shell
source ~/.airc            # reloads clor / ocs / occli
loadout check --global    # must be clean — the pre-commit hook runs it
```

`loadout sync` writes outside `~/wrksp`, so it needs `claude-raw` or a shell the
sandbox does not cover. If it fails on a grant, report it — do not relocate files.

Then confirm what landed:

```bash
grep -n "MODEL=\|CLOR_MODEL:-" .airc.d/claude.zsh   # 4 model slots + the start alias
grep -n "openrouter/" .airc.d/opencode.zsh .airc.d/llmcli.zsh loadout/skills/second-opinion/SKILL.md
python3 -c "import json;d=json.load(open('loadout/settings/pi.json'));print(d['defaultModel'],d['defaultThinkingLevel'],d['enabledModels'])"
```

Confirm the start alias resolves to the default tier — that is the one edit with
no model id in it, so a stale value survives every id-based check.

Report the diff summary and leave the commit to the user.

## Examples

### Example 1: Routine refresh

User says: "refresh the model tiers"

1. Run `rank_models.py`. Frontier comes back
   `GPT-5.6 Luna ($0.049, 46.9) → GLM-5.3-Flash ($0.087, 58.2) →
   GLM-5.3 ($0.683, 59.1) → Claude Opus 5 ($2.337, 59.2)`, with a cliff flagged
   after GLM-5.3 at $23.23 per extra agentic point.
2. Three frontier points sit below the cliff, so they *are* the ladder: low =
   GPT-5.6 Luna (max), mid = GLM-5.3-Flash (max), high-main = GLM-5.3 (max).
   Luna is a frontier lab but takes low cleanly — the best alternative near its
   price is MiniMax-M3 at 36.1 agentic for $0.139, so Luna is 10.8 points
   stronger *and* 2.8x cheaper. high-fallback = Qwen3.8 2.4T A95B — different
   lab, 57.1 agentic at $0.807, beating Kimi K3 on both axes.
3. Run the four sanity checks. Costs rise across the ladder ✓, no pick is
   dominated ✓. But check 3 fires: Luna costs **more per input token** than mid
   ($0.20/M vs $0.15/M) and only wins `$/task` on terseness (136k tokens/task vs
   700k). So **mid holds the default** — low keeps `occli` and the haiku rung.
4. Present the four with runners-up, the default-tier call, and the binding
   table. Wait.
5. On approval: the six targets, `loadout sync --global`, `source ~/.airc`,
   `loadout check --global`.

Result: pi, OpenCode and `clor` default to GLM-5.3-Flash; `clor` opens on
`sonnet` so it lands on that default; subagents take it too; `occli` and the
haiku rung keep Luna; the two second-opinion advisors sit on different labs.

### Example 2: Read-only question

User says: "what is clor running right now?"

Read `.airc.d/claude.zsh` and report the three tier mappings. Do not run the
ranking or edit anything — this is a question, not an instruction to re-pick.

## Troubleshooting

### `rank_models.py` returns few or no models

**Cause:** Artificial Analysis changed its payload shape, so the brace-matched
`"agenticIndex"` records no longer parse.
**Solution:** Re-run with `--no-cache` first — a truncated cached fetch looks the
same. If still empty, inspect the cached HTML under `$TMPDIR/agent-models/` for
`self.__next_f` and `agenticIndex`. Report that the parser needs updating rather
than falling back to reading the rendered chart, which has no numbers in it.

### A model is excluded as "no OpenRouter id"

**Cause:** Either it genuinely is not on OpenRouter, or the AA and OpenRouter
names differ by more than the resolver's fallbacks handle.
**Solution:** Check by hand against `https://openrouter.ai/api/v1/models`. If it
exists, extend `resolve()` in the script. Never paste an id you have not seen in
that API response — `deepseek/deepseek-v4-pro` and
`deepseek/deepseek-v4-pro-0813` are different builds, and the plain-looking one
is the older one.

### Pi warns `Model "…" not found for provider "openrouter"`

**Cause:** Pi's cached model catalog predates the model. It still runs, using the
id verbatim.
**Solution:** `pi update` refreshes the catalog. Do not hand-edit
`~/.pi/agent/models-store.json` — Pi overwrites it.

### OpenCode still runs the old model after editing

**Cause:** `loadout/settings/opencode.json` is a loadout *source*. The file
OpenCode reads is `~/.config/opencode/opencode.json`, which is generated.
**Solution:** Run `loadout sync --global` from an unsandboxed shell. Never edit
the generated file — `loadout check --global` rejects the drift at commit.
