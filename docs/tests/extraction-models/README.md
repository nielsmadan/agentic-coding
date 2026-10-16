# Extraction model benchmark

Current default: **Google Gemini 2.5 Flash-Lite** (`google/gemini-2.5-flash-lite`).
Current fallback: **Google Gemini 3.1 Flash-Lite** (`google/gemini-3.1-flash-lite`).
These remain unchanged until a measured selection is approved.

`bin/extraction.py` owns the prompt, fencing, model defaults, OpenRouter request
and fallback. `jina-fetch` supplies fetched pages; `distill` supplies files or
stdin. Neither CLI launches the other. Both resolve imports from the real script
path, including when invoked through a symlink.

## Small repeatable suite

```sh
python3 benchmark/bench-models.py --small benchmark/extraction-candidates.txt benchmark/runs/YYYY-MM-DD-extraction --repeats 3 --workers 3 --budget 5 --timeout 60
```

Choose a new output directory on every run; existing results are never overwritten.
Requires the injected `OPENROUTER_API_KEY`; fixtures are synthetic and need no Jina
fetch or private data. Refresh the candidate list against OpenRouter's catalog,
including the default and fallback controls and at most four challengers.
`extraction-candidates.txt` records the six models used for the initial run, not a
permanent recommendation. Candidates must support at least 128k context; Grok/xAI
are excluded. The runner saves live prices and distinct endpoint providers.

Eight fixed cases cover a relevant answer, an irrelevant question, a misleading
partial subject match, verbatim sentences, verbatim code, a fact inside a ~200k
character log, two labelled documents, and embedded malicious instructions.
The quote/code graders require exact text: inspect failed answers before treating
a formatting failure as fabrication. The sentinel tests require the exact first
line and at most one explanation line. Manual review must still check that the
explanation does not answer the wrong question. The suite is a regression screen,
not evidence of universal extraction accuracy.

Three repetitions per model produce 144 calls. Order is shuffled with seed 42;
up to three requests run at once, in batches. There are no discarded warmup calls:
first-call setup and provider/cache variation remain in the reported latency.
Compare runs only at equal concurrency, repetitions and fixtures; median and
maximum latency are descriptive, not statistical guarantees.

The benchmark uses the exact production request function, with fallback disabled
and no reasoning override. Model-provider defaults therefore apply. It saves full
answers, finish reasons, response model IDs, usage and reported cost in
`responses.jsonl`; fixture snapshots and hashes, source hashes, settings, prices
and providers in `fixtures.json` and `metadata.json`; and aggregate quality,
errors, latency and cost in `summary.json`. Re-grade stored answers instead of
paying to rerun when a grader changes. A missing cost is unknown, never zero.

Before each batch the budget guard reserves an upper estimate from UTF-8 source
bytes plus prompt overhead and the catalog context limit as an output ceiling,
using the largest advertised input/output price including overrides. Completed
calls use reported cost; calls with unknown cost retain their reservation. It
stops before starting an unaffordable batch and writes an incomplete summary.
This is a client-side guard, not an OpenRouter account spending cap: prices can
change and in-flight requests may still bill after timeout. Inspect unknown-cost
calls and provider metadata before proposing another run.

## Selection and application

The `agent-models` skill includes this benchmark on a full refresh; `--extraction`
selects only this workflow and `--coding` skips it. Reject fabricated quotes and
wrong-subject answers, then compare quality, latency, actual cost and provider
availability. A fallback with the same providers covers model-specific failures,
not an outage affecting those providers. Present the full model names and exact
IDs and wait for approval before changing the two constants in
`bin/extraction.py`. Both CLIs pick them up immediately on the next invocation.

## Recorded runs

- [2026-10-14 initial shared-extraction run](runs/2026-10-14-initial.md): baseline
  for the small suite; proposed default change awaits approval.

## Legacy suite and historical evidence

The existing `extract5`, `complex6`, `relevance`, and `all` modes remain available:

```sh
python3 benchmark/bench-models.py benchmark/models.txt all /tmp/extraction-legacy
```

They fetch public source pages through Jina and cache them in the output directory.
The old model list needs catalog validation before reuse. Their historical CSV
format remains unchanged; use the small suite for durable raw-response records.
[`extract-model-result.csv`](../../../benchmark/extract-model-result.csv) retains the historical five-model cohort. The lessons
below describe those historical runs, not current model measurements.

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

`relevance` — three off-topic questions with **no escape hatch offered**, plus a control that
must still be answered. This is the suite that matters most; run it on any candidate before
looking at cost. `offtopic-compound` is the production failure shape: the page genuinely has
"an accepted answer", just not on the subject asked about, and a weak model answers with the
wrong one. The control exists because a model that refuses everything would ace the rest.

`extract5` — types (list the Redis data types), why (one-sentence cause), needle-date and
needle-views (facts buried in 209k chars), trap (asks for a Rust crate the page never
mentions; must decline on its own, with no hint that declining is an option).

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
10, 3, 2, 2 against a truth of 4; `claude-haiku-4.5` also said 2). Treat that as a property of
the approach: counting or enumerating occurrences across a long page belongs in `grep -c`, not
in a prompt. The global web-fetching guidance says so for this reason.

**Distinguish fabrication from non-compliance when reading an anchors failure.** Both score 0,
and they mean opposite things. `gpt-oss-120b` invented a quote that appears nowhere on the
page — a trust failure, disqualifying. `claude-haiku-4.5` failed the same task by ignoring
"no commentary", opening with "I've reviewed the document carefully…" and then returning only
one usable phrase — an instruction-following failure, annoying but honest. Always print the
answer and check each line against the page before deciding which one you are looking at.

## How this benchmark certified a bad model

The first run's trap task read:

> Which Rust crate does this page recommend for branchless programming?
> **If the page does not mention one, reply exactly: NOT IN DOCUMENT**

Every model passed. The bolded clause is why — it *told the model the escape hatch existed*.
Real callers never write that. Asked the way a caller actually asks, the winning model answered
off-topic questions with real, correctly-attributed quotes from the page: **7 failures in 23
trials**, where every other model tested failed none. It shipped, and it was caught in
production during a research pass, not here.

The general lesson, worth applying to any new task added below: **a task where every model
passes is not evidence that the models are good, it is evidence the task is too easy.** Treat a
clean sweep as a bug in the task until proven otherwise.

Two other things the failure exposed, now owned by `bin/extraction.py`:

- **No temperature was set**, so extraction inherited the provider default. The same model and
  prompt gave 2/5 on one batch and 5/5 on the next. `TEMPERATURE = 0` in both files now.
- **The system prompt had no sentinel for irrelevance.** It said "if they do not contain the
  answer, say so", which a model can satisfy while still answering a differently-scoped
  question. It now mandates `NO_RELEVANT_CONTENT`, and `jina-fetch` surfaces that on stderr.

Both CLIs and both benchmark modes import the production request implementation from
`bin/extraction.py`.
Under the fixed prompt and temp 0, every model tested scores 4/4 on `relevance` — including
the one that failed in production, which is exactly why the model choice is no longer made on
that suite alone. `ling-2.6-flash` is not reinstated: it took 302.8s for those four tasks under
Novita rate-limiting, and one clean pass does not undo a 7-in-23 failure record.

## Columns in extract-model-result.csv

`run_date, suite, model, providers, passed, of, time_s, cost_usd, failed`

`providers` is the distinct OpenRouter endpoint count from step 2, blank where not measured.
`time_s` and `cost_usd` are for the whole suite, not per task. `failed` is a
semicolon-separated list of task names, empty on a clean sweep.
