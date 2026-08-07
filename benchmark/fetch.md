# Benchmark: WebFetch vs Jina

Agent instructions for rerunning the page-fetch benchmark. Results go in
`fetch-result.csv` (append a new `run_date`, do not overwrite prior runs).

Runs: 2026-07-29 (v1, 28 URLs), 2026-08-03 (v2, current). v1's URL set was replaced
outright — see "Choosing URLs" for why. Written up in
`~/wrksp/notes/work/blog/entries/i-tried-jina-so-you-dont-have-to.md`.

## The one thing to understand first

**There are three arms, not two, and only two of them are comparable.**

| arm | what it does | returns |
|---|---|---|
| **A** `WebFetch` | fetch → summarise with a small model | an answer |
| **B** `mcp__jina__read_url` | fetch → convert to markdown | the whole page |
| **C** `jina-fetch` | fetch → summarise with a small model | an answer |

A vs B measures *summarising vs not summarising*. It is architecture, not quality,
and B loses by ~40×. Say so in any writeup. **A vs C is the real comparison** — both
summarise, and it is the choice you actually make.

v1 only ran A vs B and presented it as a verdict on Jina. That was the main flaw.

## Choosing URLs

Derive them from actual usage, not from intuition. Parse `~/.claude/projects` **and**
`~/.local/share/ringleader/archive` (see `check-claude-projects`; the archive holds
more transcripts than the live dir and archiving *moves* files, so a live-only scan
silently under-reports by ~40%).

Two filters that matter:

1. **Drop project-bound research sweeps.** One project doing a big one-off research
   push will dominate the host ranking. Compute, per host, the share of fetches from
   its top project — ≥80% means it is that project's research, not your workload.
   v1's set was 22% representative; whole buckets (yelp, g2, quora, nytimes,
   instagram, linkedin, allrecipes, bonappetit) had **zero** organic use.
2. **Docs sites are project-bound by nature and still belong.** Every docs host in
   the ranking is ≥97% one project, because projects need their own docs. The
   category is 23% of traffic across ~92 hosts. Sample by **generator** (rustdoc,
   Sphinx, MkDocs, Hugo, JS SPA), since that is what HTML-to-markdown must cope with.

The v2 set: github.com, raw.githubusercontent.com, code.claude.com,
news.ycombinator.com (cross-project, 7–30 projects each) plus developer.apple.com,
docs.rs, docs.ansible.com, chezmoi.io, docs.railway.com, kubernetes.io (docs, by
generator).

## Choosing queries

**Lift them verbatim from the transcripts.** Do not write your own — invented queries
drift toward whatever you expect the tools to do. The measured distribution across
2,349 real prompts: median 189 chars, **53% demand verbatim/quoted text**, 6% ask to
summarise. `DEFAULT_PROMPT` ("Summarize this page.") is effectively dead code.

## Procedure

1. **Reference copies first.** `jina-fetch --no-cache --raw --out ref/<host>.md <url>`
   for every URL. This is arm B's payload and the corpus for any grading.
2. **Arm C** is scriptable — run the 10 in parallel, time each with bash wall clock.
3. **Arm A** must be issued as real `WebFetch` tool calls. Save each answer to a file
   to get exact character counts; do not eyeball them (v1 did, and compared an
   eyeballed estimate against an exactly-measured one).
4. **Tokens** = chars ÷ 4 for all three arms, same method throughout.
5. **Timing** — see the trap below. Use URLs not fetched this session (WebFetch caches
   15 min per URL).

## Traps

- **`mcp__jina__read_url` ≠ `jina-fetch --raw`.** The MCP applies extra cleanup; on
  one sample it returned 55% fewer chars than r.jina.ai's markdown for the same page.
  Pick one and label the column for what it is. v2 uses the r.jina.ai markdown, which
  is what v1 measured, so the trend line survives.
- **Do not benchmark Jina via unauthenticated `curl https://r.jina.ai/<url>`.** Rate
  limited, behaves differently from the authenticated path.
- **Jina strips `www.`** — verify a suspected failure against both forms.
- **Jina does not bypass paywalls**, despite the tool description.
- **A page's reference copy can be invalid.** If Jina returned chrome only (see
  github.com below), you cannot grade *anything* against that reference, including
  WebFetch — its content is simply absent from the corpus.

### Timing is not cleanly measurable for arm A

`jina-fetch` can be timed with bash wall clock around the subprocess: **1.34s/page**
for a cold parallel batch of 5.

`WebFetch` can only be timed by bracketing turns — timestamp, batch, timestamp, minus
two harness hops. That gives **3.46s/page**, but the number includes agent-side
generation time and the cost of streaming results into context, and **the hop is not
constant**: it scales with response size, which v1's fixed-hop subtraction assumes it
does not. Report both with their methods stated. Do not publish a ratio.

### Verbatim fidelity: attempted and abandoned

The intent was right — 53% of real queries demand exact text, so "does the quoted
span actually occur in the page" is the axis that matters. Three grader bugs killed
it, in order of discovery:

1. **Exact matching punished reformatting.** The page has `` `state=present` ``;
   WebFetch quoted it without backticks. Scored 0/10 on ansible; really 7/10. Strip
   markdown markers from both sides.
2. **The quote regex mispaired quotes.** `"([^"]{25,})"` skips a short quoted span,
   then re-anchors on its *closing* quote and captures the junk *between* two real
   quotes as if it were one. This systematically punished answers containing more
   quotes — precisely what was being measured. Split on `"` and take odd segments.
3. **Structural asymmetry no fix removes.** WebFetch marks quotes with `"`;
   `jina-fetch` usually returns extracted text unquoted or in backticks. The two are
   not comparable on this axis at all.

Do not publish a fidelity number without solving (3). Given this benchmark's history,
a clean-looking result is more likely a fourth undetected grader bug than a finding.

## Results — 2026-08-03

**Tokens.** Median: WebFetch 309, `jina-fetch` 297, Jina raw markdown 9,340.
Across all 10 pages: 4,488 / 6,308 / 184,734 — raw markdown is **41×** WebFetch.
A and C are comparable on median; C is more verbose on two pages (HN 7×, ansible
1.8×) and cheaper on the two largest.

**The two tools fail in opposite directions, and both failures are silent-ish:**

- **Jina is blind on `github.com/blob/`** — 7,529 tokens of nav chrome, Copilot
  marketing, file tree, "Uh oh! There was an error while loading", and **no README
  body**. WebFetch returned the real content. This is the single most-fetched host
  (522 fetches). Jina is not a fallback for GitHub blob pages.
- **WebFetch truncates long pages.** On the Kubernetes Deployment page it refused:
  *"I cannot find a verbatim quote … the content ends with [Content truncated due to
  length…]"*. `jina-fetch` answered the same question correctly from the full page.

**`jina-fetch` declined 3 of 10, and all three declines were right:** github.com
(Jina handed it chrome), docs.railway.com (WebFetch independently agreed the page
does not cover it), developer.apple.com (unanswered forum thread — and WebFetch
manufactured an "## Actual Root Cause" section for it). Zero false negatives.

## Use `gh` for GitHub, not either fetcher

`gh api repos/<owner>/<repo>/contents/<path> -H "Accept: application/vnd.github.raw"`
returned the exact README that Jina could not see, in **0.6s**. On the same file:
Jina 7,529 tokens of chrome, WebFetch a 317-token summary, `gh` the actual bytes.

**480 of 522 (92%)** github.com fetches were `gh`-replaceable: repo roots 189
(`gh repo view`), issues 126 (`gh issue view`), blobs 105 (`gh api`), releases 51
(`gh release`), pulls 9 (`gh pr view`).

**A `gh-fetch` wrapper with an extractor is not worth building.** Measured over 377
real `gh` calls: median **258 tokens**, p90 1,169, and only **3%** exceed 2k. That is
already smaller than WebFetch's summariser output (309 median), so an extractor would
add a model call, latency and cost to the 97% of cases where the raw output is
smaller than the extract would be. For the tail, `--json field,field --jq '...'`
filters deterministically and for free — strictly better than an LLM over JSON.
For scale: every `gh` call ever made totals 181,447 tokens, less than the 184,734
that ten Jina raw page reads cost in this one run.

## Columns in fetch-result.csv

`run_date, host, url, webfetch_tokens, webfetch_outcome, jinafetch_tokens,
jinafetch_outcome, jinafetch_time_s, jina_raw_tokens, raw_vs_webfetch`

Outcomes: `ok`, `ok_overclaimed` (answered beyond what the page supports),
`declined_correct`, `declined_defensible`, `truncated`, `thin`, `blocked_robots`,
`http_403`, `captcha`, `soft_404`, `empty`, `not_tested`.
