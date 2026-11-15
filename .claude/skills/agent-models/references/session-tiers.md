# Session tiers

`claude <tier>`, `codex <tier>`, and `pix <tier>` accept `low`, `mid`, `high`,
`xhigh`, or `max` as the first argument. The tier selects both model and effort
for that invocation. `mid` is the tier name; `medium` is an effort value.
This selection is part of every normal agent-models refresh, sharing its proposal,
approval, application and verification steps.

## Scope and targets

The single source of model/effort pairs is `.airc.d/07-model-tiers.zsh`:

| Table | Consumers | Native arguments |
|---|---|---|
| `anthropic` | `claude` | `--model <id> --effort <effort>` |
| `openai` | `codex`, `pix` | Codex: `--model <id> -c 'model_reasoning_effort="<effort>"'`; pix: `--provider openai --model <id>:<effort>` |

Only Anthropic and OpenAI are eligible here. This scope does not update Cursor
(`agent` / `cursor-agent`), plain `pi`, `picc`, `clor`, OpenCode, advisor profiles,
extraction models, or global model defaults. Preserve no-tier invocation behavior,
authentication, sandbox routing and iTerm tracking. Codex and pix share a table;
report that shared binding when only one is named in a refresh request.

## Rank and select

Run the requested lab's ranking, or both for a full session refresh:

```sh
python3 .claude/skills/agent-models/scripts/rank_models.py --ladder anthropic
python3 .claude/skills/agent-models/scripts/rank_models.py --ladder openai
```

`--json` includes the scores, costs, frontier and marginal cost per index point.
`--no-cache` refreshes the source pages. These modes do not query OpenRouter or
apply the OpenRouter token-price cap or alternative-lab preference.

Treat each model/effort pair as a separate candidate. Compare Intelligence Index
against **cost per Intelligence Index task**, including reasoning costs. Token
prices alone do not decide these tiers. Read the frontier and cost cliffs within
each lab, and preserve the user's capability bands when choosing among alternatives.
Use the cheaper per-task candidate within a band unless the user asks to trade up.
Keep intelligence and cost increasing across the ladder; flag dominated selections.
When the user explicitly picks one anyway, retain it and record the exception.

`max` is the deliberate highest-capability option even beyond a cost cliff. Show
its premium rather than silently lowering it. For the other tiers, prefer points
before cliffs; repeating a model at different efforts is fine. AA's task cost is
a benchmark comparison, not a forecast of subscription usage or this user's bill.

Verify native model IDs and supported effort levels in the installed CLIs/catalogs
and current official documentation. AA release slugs are not necessarily native IDs
(`gpt-6-1-sol` versus `gpt-6.1-sol`), and OpenRouter IDs are not native Anthropic IDs.
Pi's `--offline --list-models` checks its catalog without refreshing it. Do not read
auth files or print credentials. An unavailable model or unsupported effort is a
blocker for that pick, not permission to silently substitute another effort.

Present the five picks per lab with score, task cost, effort, runners-up and cliffs.
If the user already specified the picks or authorized choosing the cheaper named
alternatives, apply within that authorization. Otherwise obtain approval of the
concrete table before changing the presets.

## Apply and verify

Update the relevant table in `.airc.d/07-model-tiers.zsh` and the current selection
below. Update README's shortcut table if mappings change. The wrappers only translate
the pair into native flags; do not duplicate the ladder in each wrapper.

Run the Python formatter on edited Python files, then:

```sh
for file in .airc.d/{07-model-tiers,claude,codex,pi}.zsh; do zsh -n "$file" || exit; done
timeout 60 python3 -m unittest discover -s tests -p 'test_model_tiers.py'
timeout 60 python3 -m unittest discover -s .claude/skills/agent-models/scripts -p 'test_rank_models.py'
```

The shell tests stub launchers, so they check argument forwarding without starting
paid model sessions. If changing supported model/effort behavior, also verify the
native CLI's capabilities; do not claim a stub test proves server acceptance.

These sources are read directly through `.airc` and the project skill symlink;
no loadout sync is needed. Reload with `source ~/.airc` in the user's shell.

## Current selection — 2026-11-15

Measured from the [AA leaderboard](https://artificialanalysis.ai/leaderboards/models)
and [model details](https://artificialanalysis.ai/models) RSC records on this date.
The script's `fetch()` caches those pages under `$TMPDIR/agent-models/`.

| Lab | Tier | Native model | Effort | Intelligence | USD/task |
|---|---|---|---|---:|---:|
| Anthropic | low | claude-haiku-5-5 | xhigh | 34.64 | 0.248 |
| Anthropic | mid | claude-sonnet-5-5 | high | 41.52 | 1.636 |
| Anthropic | high | claude-opus-5-5 | high | 51.84 | 3.465 |
| Anthropic | xhigh | claude-fable-5-2 | medium | 56.41 | 3.803 |
| Anthropic | max | claude-fable-5-2 | max | 64.56 | 26.539 |
| OpenAI | low | gpt-6.1-sol | low | 34.80 | 0.161 |
| OpenAI | mid | gpt-6.1-sol | medium | 46.35 | 0.359 |
| OpenAI | high | gpt-6.1-sol | xhigh | 52.46 | 0.764 |
| OpenAI | xhigh | gpt-6.1-sol | max | 54.61 | 1.272 |
| OpenAI | max | gpt-6-astra | max | 56.85 | 6.245 |

The Anthropic ladder follows the user's explicit choices. Opus high is dominated
by Fable low (53.92 at $3.097); flag that alternative on the next refresh.

OpenAI choices use the cheapest of the user's named alternatives: Terra medium
is $0.169 at 38.17 versus Sol low at $0.161; Terra xhigh is $0.401 at 45.25 versus
Sol medium at $0.359. Sol xhigh beats Terra max ($0.961, 51.33) and Astra medium
($2.732, 51.55) on both axes. Astra high costs $3.239 for 54.85 versus Sol max's
$1.272 for 54.61. Astra max is 4.91× Sol max's cost for 2.25 more points; Fable max
is 6.98× Fable medium's cost for 8.16 more points. These are intentional max-tier
premiums, not value-tier recommendations.
