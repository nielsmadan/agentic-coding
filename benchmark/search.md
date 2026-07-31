# Benchmark: Jina search vs built-in WebSearch

Agent instructions for rerunning the search benchmark. Results go in `search-result.csv`
(append a new `run_date`, do not overwrite prior runs).

First run: 2026-07-29, second round 2026-07-30. Written up in
`~/wrksp/notes/work/blog/entries/i-tried-jina-so-you-dont-have-to.md`.

## The headline finding to re-verify

The built-in WebSearch returned **zero** Stack Overflow, Stack Exchange or Reddit results
across 15 queries. Jina returned 25. This is not a ranking difference: those domains are
excluded from WebSearch's index by the same crawler policy that makes WebFetch refuse them.

Re-verify that mechanism first (step 1 below). It is one call and it either still holds or
the whole conclusion has changed.

## Prerequisites

- Jina MCP (`mcp__jina__search_web`, `mcp__jina__parallel_search_web`).
- `WebSearch` (deferred; `ToolSearch("select:WebSearch")`).

## Procedure

### 1. Probe the crawler blocklist (do this first, it is cheap and decisive)

`WebSearch` takes `allowed_domains`. Passing a blocked domain returns a 400 that **enumerates
which domains are barred**, so you can map the blocklist directly:

```
WebSearch(query="test query for domain accessibility",
          allowed_domains=["stackoverflow.com","reddit.com","serverfault.com",
                           "youtube.com","github.com", ...])
```

Response shape:

```
400 The following domains are not accessible to our user agent:
['serverfault.com', 'stackoverflow.com', 'reddit.com']
```

Batch 12 to 15 domains per call. As of 2026-07-29:

- **Blocked:** stackoverflow.com, reddit.com, serverfault.com, superuser.com, askubuntu.com,
  mathoverflow.net, stackexchange.com, seriouseats.com, allrecipes.com, bonappetit.com,
  epicurious.com, nytimes.com, wsj.com, theverge.com, arstechnica.com
- **Not blocked:** youtube.com, news.ycombinator.com, dba.stackexchange.com,
  devops.stackexchange.com, linkedin.com, medium.com, quora.com, yelp.com, instagram.com,
  x.com, g2.com, github.com, gitlab.com, dev.to, hashnode.com, substack.com

Note the oddity: `stackexchange.com`, `superuser.com`, `askubuntu.com` are blocked while
`dba.stackexchange.com` and `devops.stackexchange.com` are not. Recheck whether that is still
true, it may be per-host robots.txt or a curated list.

### 2. Run the same queries through both tools

Take queries from `search-result.csv`. Keep the existing ones for comparability. Use
`num: 10` on the Jina side to match what WebSearch returns (roughly 6 to 10 links).

Use **fresh queries** for any round you intend to time.

### 3. Count results by domain

Per query, per tool, record:

- `*_results`: total results returned
- `*_community`: how many were Stack Overflow, the Stack Exchange network (serverfault,
  superuser, askubuntu, dba.stackexchange, ...), or Reddit. These are the confirmed-blocked
  sources, which is what makes the count meaningful.
- `jina_hackernews`: **separate column on purpose.** Hacker News is a link aggregator, not a
  Q&A site, and it is *not* blocked. WebSearch still never returns it, so its absence is a
  ranking artifact and must not be folded into the blocklist argument.

### 4. Measure speed per batch of five, never per query

A single search takes about a second; the harness adds ~4.8s per hop between tool calls with
a second or two of variance. Per-query timing is below the noise floor. Baseline a hop, then:

```
timestamp -> 5x WebSearch (parallel) -> timestamp -> 1x parallel_search_web (5 queries) -> timestamp
```

The middle timestamp serves as both the WebSearch end and the Jina start. Each side then
includes two hops; subtract them. Run at least two rounds with different queries, since one
round is a single sample.

Measured so far:

| Round | WebSearch | Jina | Ratio |
| --- | --- | --- | --- |
| 1 (2026-07-29) | ~9.6s | ~5.4s | 1.8x |
| 2 (2026-07-30) | ~11.5s | ~6.4s | 1.8x |

Token cost is roughly a wash (WebSearch slightly heavier, since it returns a synthesised
prose answer on top of the links). Nothing like the ~16x gap on the fetch side.

## Capability differences to re-check

| | WebSearch | Jina |
| --- | --- | --- |
| Geography | **US only** | `gl`, `hl`, `location` all work |
| Domain filtering | `allowed_domains` / `blocked_domains` | none |
| Per-result metadata | title + URL only | title, URL, snippet, date, source engine |
| Output | synthesised prose answer + links | raw results |
| Time filter | none | `tbs` (`qdr:h/d/w/m/y`) — **still untested** |

Geo check that worked: rerun a consumer query with `gl=de, hl=de, location=Berlin`. On the
first run this localised the dates to German relative form ("vor 1 Jahr") and surfaced UK/EU
sources absent from the US-default run.

## Traps

- **`num` is a ceiling, not a target.** The default is 30 but you get what the engine has.
  Rerunning a query at `num: 30` returned the identical 9 results as `num: 10`. Do not report
  the default as a token trap.
- Do not benchmark Jina search via curl. `s.jina.ai` needs the API key, which the agent
  should not go looking for, and the unauthenticated reader endpoint is not representative.
- What fills the gap left by blocked domains is often a crawlable restatement of the same
  content (codemia.io, tildalice.io reposting Stack Overflow; answeroverflow.com mirroring
  Discord). Worth spot-checking, it is the most interesting qualitative finding.

## Columns in search-result.csv

`run_date, round, query, websearch_results, websearch_community, jina_results,
jina_community, jina_hackernews, timed, round_websearch_time_s,
round_websearch_tokens_est, round_jina_time_s, round_jina_tokens_est`

Round-level timing is repeated on each row of that round (denormalised for CSV convenience).
Rows with `timed=no` were run for result quality only; their timing columns are blank.
