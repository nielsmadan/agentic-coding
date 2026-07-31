# Benchmark: Jina Reader vs WebFetch

Agent instructions for rerunning the page-fetch benchmark. Results go in
`fetch-result.csv` (append a new `run_date`, do not overwrite prior runs).

First run: 2026-07-29. Written up in `~/wrksp/notes/work/blog/entries/i-tried-jina-so-you-dont-have-to.md`.

## Why this exists

Both tools change over time. WebFetch in particular improved a lot between Feb and Jul 2026
(it did not strip `<style>`/`<script>` until 2.1.105 on 2026-04-13). Rerun this before
trusting any older conclusion about which tool to reach for.

## The one thing to understand first

**These tools are not the same shape, and the token numbers are not directly comparable.**

- WebFetch: fetch HTML, convert to markdown, run a small fast model over it, return **only
  that model's answer**.
- Jina `read_url`: fetch HTML, convert to markdown, return **the whole markdown**.

Both do HTML to markdown. The difference is the summarising step. So WebFetch will always
look cheaper on tokens, and that is architecture, not quality. Say so in any writeup.

## Prerequisites

- Jina MCP available (`mcp__jina__read_url`, `mcp__jina__parallel_read_url`), or `jina-fetch`
  on PATH for the extract-only path.
- `WebFetch` available (it is a deferred tool; load with `ToolSearch("select:WebFetch")`).
- Do **not** try to verify `JINA_API_KEY` with `env | grep`. The sandbox classifier blocks it
  and it looks like secret probing. Auth is injected automatically by the `claude` zsh wrapper.

## Procedure

1. **Take the URL list from `fetch-result.csv`** (the `url` column). Add new URLs if testing
   something new, keep the existing ones so runs stay comparable.

2. **Call both tools on each identical URL with an identical prompt.** The prompt must make
   silent failure detectable, e.g.:

   > Return the page title and the first 80 words of the main content verbatim.
   > If the page content is not available, say exactly: BLOCKED_OR_EMPTY and describe what you got.

   Without that last clause you cannot tell "worked" from "returned the nav bar".

3. **Record an outcome per tool** using this vocabulary:

   | Value | Meaning |
   | --- | --- |
   | `ok` | content returned |
   | `ok_paywalled` | free portion returned, paywall reached |
   | `ok_basic` | worked but returned noticeably less than the other tool |
   | `ok_overran` | worked but ignored the length limit and dumped the page |
   | `partial_paywalled` | article body yes, the actual payload (recipe, etc.) paywalled |
   | `thin` | HTTP 200, chrome only, article body missing |
   | `blocked_robots` | WebFetch: "Claude Code is unable to fetch from X". Request never sent |
   | `http_403` / `http_402` | origin refused at fetch time |
   | `redirect_refused` | WebFetch returned instructions instead of following a cross-host redirect |
   | `captcha` | anti-bot interstitial |
   | `soft_404` | a "page not found" page for a URL that exists |
   | `empty` | empty string returned |
   | `wrong_content` | returned something unrelated (NYTimes gave a 1x1 tracking pixel) |
   | `not_tested` | not run this round |

4. **Measure Jina payload size exactly, not by eye.** Large `parallel_read_url` results blow
   the tool-result token ceiling and get spilled to a file. Measure there:

   ```
   jq -r 'to_entries[] | "\(.key)|chars=\(.value.text|length)"' <persisted-file>
   ```

   Estimate tokens as `chars / 4`. Note in the writeup that this is an estimate.

5. **Measure speed per batch, never per URL.** The harness adds roughly 4.8s of overhead per
   hop between tool calls, which swamps a ~1s fetch. Baseline it first, then bracket a batch
   of five:

   ```
   python3 -c "import time; print(f'{time.time():.3f}')"    # twice, back to back, nothing between
   ```

   The delta between those two is one hop. Then `timestamp -> batch of 5 -> timestamp` and
   subtract two hops. Report as "time for a batch of five pages".

6. **Use URLs you have not fetched yet this session for the timing run.** WebFetch caches per
   URL for 15 minutes, so re-timing a URL you already hit measures the cache.

## Traps that cost time on the first run

- **Do not benchmark Jina via unauthenticated `curl https://r.jina.ai/<url>`.** It is rate
  limited and behaves differently from the authenticated MCP path. On the first run it gave
  403 for GitHub while the MCP returned 13,411 chars for the same URL. Those numbers are not
  a proxy for anything and were discarded.
- Raw HTML is a useful third column (`raw_html_chars`) for showing what the markdown
  conversion saves, but use `curl -sSL --compressed -o body` and measure the **file size**.
  `%{size_download}` reports compressed bytes, which is not comparable to a char count.
- Jina strips `www.` from URLs. Verify a suspected Jina failure against both `www` and
  bare host before blaming Jina. On the first run allrecipes/quora returned the same
  402/403 either way, so the stripping was not the cause.
- Jina does **not** bypass paywalls, despite the tool description. It returns the same free
  prefix WebFetch gets, without flagging that it stopped early.

## Columns in fetch-result.csv

`run_date, site, url, webfetch_outcome, webfetch_tokens_est, jina_outcome, jina_chars,
jina_tokens_est, raw_html_chars`

`webfetch_tokens_est` is rough: its output is prose whose length varies. `jina_chars` is
exact where it was measured with `jq`, blank where the result came back inline and was not
counted.
