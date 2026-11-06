## Web Search & Fetching

**For search, use `mcp__jina__search_web`** (or `mcp__jina__parallel_search_web` for several queries at once) rather than `WebSearch` — it returns better results. Fall back to `WebSearch` only if the Jina MCP is unavailable.

**For anything on GitHub, use `gh` — not a fetcher.** Always prefer dedicated `gh` subcommands (`gh issue view --comments`, `gh pr view --comments`, `gh release list`, `gh run list`, `gh repo view`) over `gh api`. Use `gh api --method GET repos/<owner>/<repo>/contents/<path> -H "Accept: application/vnd.github.raw"` only when fetching raw file bytes or trees not accessible via standard subcommands. HTML fetchers fail on `github.com/blob/` pages due to client-side rendering. `gh` output is structured; filter it with `--json field,field --jq '...'` rather than running a model over it.

**For fetching a known URL, use `WebFetch`.** It is the default for short pages.

**When `WebFetch` fails, use `jina-fetch <url> "<what to extract>"`** (on `PATH`). It fetches through Jina, caches the full page under `TMPDIR`, and returns only the extract. Use the direct fetch first for transactional pages (prices, stock, shipping); go straight to `jina-fetch` for long-form reading (docs, articles, reviews), which `WebFetch` truncates, and for Stack Overflow, which blocks `WebFetch`.

**Before writing that a source says something, paste the line.** A claim attributed to a document is a quote, not a summary — grep the cached file for it and reproduce the sentence. If you cannot paste it, you do not have it: say what the source does establish instead of rounding it up to what you expected. And when a page carries a canonical list (permissions, prerequisites, ordered steps), read the whole section by range rather than grepping for the items you expect, since a grep built from your expectation can only ever confirm it.

**Load the `web-fetch` skill** when a fetch fails, is refused or comes back as boilerplate, when exact text from a page matters, and before fetching Reddit or a bot-protected or paywalled site. It has the escalation ladder (up to `jina-fetch --proxy`), the failure signatures, and how to quote from the cached page. This machine has no logged-in browser: content behind a login is out of reach, so say so rather than working around it.
