# Benchmark: which model `jina-fetch` extracts with

Agent instructions for rerunning the extraction-model benchmark. Results go in
`extract-model-result.csv` (append a new `run_date`, do not overwrite prior runs).

First run: 2026-07-30. Picked `inclusionai/ling-2.6-flash` as the default in `bin/jina-fetch`,
with `deepseek/deepseek-v4-flash` as the 429/5xx fallback.

## Why this exists

`jina-fetch` is the third stage after `fetch.md` and `search.md`: Jina returns the whole page,
a small model turns it into an answer, and only the answer reaches the agent's context. That
model is a swappable parameter, and the cheap end of OpenRouter turns over fast — models are
added, superseded, and repriced monthly. Rerun before trusting the current default.

## The one thing to understand first

**Price does not track capability here, and cheap does not mean small.** On the first run the
cheapest model tested (`ling-2.6-flash`, $0.010/Mtok) had *more* active parameters than models
costing 5× more, and beat them. Sparse-MoE architecture does not explain the pricing either —
models with the same or sparser activation ratios cost 5–12× more. Assume the price is a
commercial decision that can change, not a property of the model.

What does show up in the data is output verbosity, since output bills 3–13× input. A reasoning
model spends most of its bill deliberating over a task whose answer is a 15-line list: on the
same page `ling-2.6-flash` emitted 62 output tokens, `deepseek-v4-flash` 1,710,
`qwen3.7-flash` 2,092. That is the latency difference too.

## Prerequisites

- `OPENROUTER_API_KEY` and `JINA_API_KEY` in env (injected by the `claude` zsh wrapper).
  Do **not** try to verify them with `env | grep` — that looks like secret probing.
- `jina-fetch` on PATH.
- `bench-models.py` in this folder does the whole run. It caches the source pages under
  `pages/`, so reruns cost model tokens only.

## Procedure

1. **Refresh the candidate list.** Cheap models appear and vanish monthly, so do not just
   reuse `models.txt`. Pull the catalog and filter:

   ```
   curl -sS https://openrouter.ai/api/v1/models
   ```

   Keep text models with `context_length >= 128000` (a 200k-char page is ~50k tokens) and
   input price under ~$0.11/Mtok. Add the incumbent default and fallback as controls.

2. **Get the provider count for each candidate** — the catalog does not include it:

   ```
   curl -sS https://openrouter.ai/api/v1/models/<author>/<slug>/endpoints \
     -H "Authorization: Bearer $OPENROUTER_API_KEY"
   ```

   Count distinct `provider_name`. This is a first-class selection criterion, not trivia: a
   single-provider model is one upstream rate limit away from failing. On the first run a
   benchmark call died with `HTTP 429 — ling-2.6-flash is temporarily rate-limited upstream
   (Novita)`. It is why `jina-fetch` has a fallback model at all.

3. **Run both suites.**

   ```
   ./bench-models.py models.txt all .
   ```

   `extract5` asks whether the model can read the page at all. `complex6` asks whether it can
   be trusted for real work. Run both — `extract5` alone does not discriminate (13 of 17
   models scored 5/5 on the first run).

4. **Establish ground truth with `grep`, never from memory.** Every predicate in
   `bench-models.py` checks against a string verified present (or absent) in the cached page.
   The count-tables answer of 4 comes from `grep -c 'Branchless - Random data'`.

5. **Record cost from OpenRouter, not from list prices.** The harness sends
   `usage: {include: true}` and reads `usage.cost` back.

6. **Append a row per model+suite** to `extract-model-result.csv`.

## Traps that cost time on the first run

- **Normalise unicode before any substring check.** `gpt-oss-120b` answers with U+202F NARROW
  NO-BREAK SPACE, so `"3.5 day" in text` was False for the correct answer
  `3.5 days … eight NVIDIA P100 GPUs`. That cost it a task and understated it as 3/6 when it
  is 4/6. `nz()` in the harness handles this; keep using it for any new predicate.
- **Do not accept a substring anywhere in the response.** The count task originally passed on
  any `4` in the text, so a model that reasoned aloud could pass on a stray digit. Parse the
  *final* number instead. Print every answer and re-grade the stored text rather than
  re-running — three grader bugs on the first run, all of which moved a verdict.
- **Do not require exact adjacency.** An early check wanted `eight P100` with nothing between
  and rejected `eight NVIDIA P100`.
- **Token counts are not comparable across models.** The same 209k-char page counted between
  56,824 and 70,950 prompt tokens depending on tokenizer, so cost comparisons are approximate.
- **One run per data point is noise.** A one-task gap between two models means nothing; only
  act on the large gaps. `ling-2.6-flash` answered the counting task `10` on one run and `2`
  on a rerun.
- **Watch for free tiers with an expiry.** `ling-3.0-flash:free` scored 5/5 at zero cost, but
  Ant Group's press release ends free API access on 2026-08-03. Not a foundation to build on.

## What the suites test

`extract5` — types (list the Redis data types), why (one-sentence cause), needle-date and
needle-views (facts buried in 209k chars), trap (asks for a Rust crate the page never
mentions; must reply NOT IN DOCUMENT).

`complex6` — anchors (3 verbatim phrases, graded by matching them back against the page),
code-verbatim (reproduce 2 lines of C++), count-tables (how many tables hold a given row),
bleu-both (two numbers from a PDF), training-cost (duration + hardware), cross-doc (one
mechanism per document, two documents in one prompt).

**The anchors task is the one that matters most** and the reason `complex6` exists. It grades
verbatim fidelity, which varies far more between models than factual accuracy does, and it is
the workflow the global instructions tell agents to use (ask for anchors, then `grep` the
cached file). On the first run `gpt-oss-120b` returned
`"You are a victim of branch prediction fail."` as a verbatim quote — a sentence that appears
nowhere on the page, in any casing. A confident fake quote is the worst failure mode here,
and only this task catches it.

**Nobody can count.** Every model except `deepseek-v4-flash` failed count-tables (answers of
10, 3, 2, 2 against a truth of 4). Treat that as a property of the approach: counting or
enumerating occurrences across a long page belongs in `grep -c`, not in a prompt. The global
web-fetching guidance says so for this reason.

## Columns in extract-model-result.csv

`run_date, suite, model, providers, passed, of, time_s, cost_usd, failed`

`providers` is the distinct OpenRouter endpoint count from step 2, blank where not measured.
`time_s` and `cost_usd` are for the whole suite, not per task. `failed` is a
semicolon-separated list of task names, empty on a clean sweep.
