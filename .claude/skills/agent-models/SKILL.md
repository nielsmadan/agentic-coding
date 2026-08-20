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
| **low** | Cheapest frontier model still worth running — agentic index within ~80% of high-main. The everyday/cheap slot. |
| **mid** | A real capability or context step above low, well before the cliff. Prefer a different lab from low; a much stronger intelligence index or context window justifies picking slightly off the agentic frontier. |
| **high-main** | Highest agentic index *before* the first cost cliff. Buying past a cliff is the mistake this ranking exists to prevent. |
| **high-fallback** | Best model from a **different creator** at comparable capability — within ~6 agentic points of high-main, at similar cost. A second opinion from the same lab is not a second opinion. |

Apply the alternative-lab tiebreak: when a big-lab model and an alternative are
close in a tier, take the alternative. Take the big-lab model only when it is
clearly ahead at comparable-or-lower cost.

Note each pick's **effort** column (`max`, `xhigh`, `high`). The benchmark number
is for that effort level, so the effort has to carry into the config — a model
recorded at `max` and run at `low` is not the model that was measured.

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
grep -n "MODEL=" .airc.d/claude.zsh
python3 -c "import json;d=json.load(open('pi/settings.json'));print(d['defaultModel'],d['defaultThinkingLevel'],d['enabledModels'])"
```

Report the diff summary and leave the commit to the user.

## Examples

### Example 1: Routine refresh

User says: "refresh the model tiers"

1. Run `rank_models.py`. Frontier comes back
   `GPT-5.6 Luna ($0.047, 46.9) → DeepSeek V4 Pro 0813 ($0.252, 49.6) →
   Qwen3.8 27B ($0.326, 50.9) → GLM-5.3 ($0.683, 59.1) → Claude Opus 5 ($2.337, 59.2)`,
   with a cliff flagged after GLM-5.3 at $23.23 per extra agentic point.
2. Choose: low = DeepSeek V4 Pro 0813 (max) — cheapest credible frontier point,
   and the alt-lab tiebreak drops GPT-5.6 Luna. mid = Muse Spark 1.2 (xhigh) —
   off the agentic frontier but +4.8 intelligence index and a 1048k window over
   Qwen3.8 27B. high-main = GLM-5.3 (max) — last point before the cliff; Claude
   Opus 5 buys 0.1 points for $1.65. high-fallback = Kimi K3 (max) — different
   lab, 54.3 agentic at $0.837.
3. Present the four with runners-up, plus the binding table. Wait.
4. On approval: six edits, `loadout sync --global`, `source ~/.airc`,
   `loadout check --global`.

Result: pi, OpenCode, `clor`, `ocs`, `occli` and both second-opinion advisors
all move together, and the second-opinion advisors sit on two different labs.

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
