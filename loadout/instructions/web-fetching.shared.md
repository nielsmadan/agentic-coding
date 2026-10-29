## Web Search & Fetching

**For search, use the Jina MCP web-search tool** (and its parallel variant for several queries at once) rather than a built-in search tool — it returns better results. Fall back to the built-in only if the Jina MCP is unavailable.

**For anything on GitHub, use `gh` — not a fetcher.** Always prefer dedicated `gh` subcommands (`gh issue view --comments`, `gh pr view --comments`, `gh release list`, `gh run list`, `gh repo view`) over `gh api`. Use `gh api --method GET repos/<owner>/<repo>/contents/<path> -H "Accept: application/vnd.github.raw"` only when fetching raw file bytes or trees not accessible via standard subcommands. HTML fetchers fail on `github.com/blob/` pages due to client-side rendering. `gh` output is structured; filter it with `--json field,field --jq '...'` rather than running a model over it.

**For fetching a known URL, use your built-in fetch tool** (or `curl` for plain HTML/RSS/Atom/PDF and local dev servers). That is the default for short pages.

**When the direct fetch fails, use `jina-fetch <url> "<what to extract>"`** (on `PATH`). It fetches through Jina, caches the full page under `TMPDIR`, and returns only the extract. Use the direct fetch first for transactional pages (prices, stock, shipping); go straight to `jina-fetch` for long-form reading (docs, articles, reviews), which a summarising fetch tool truncates, and for Stack Overflow, which blocks ordinary fetching.

**Before writing that a source says something, paste the line.** A claim attributed to a document is a quote, not a summary — grep the cached file for it and reproduce the sentence. If you cannot paste it, you do not have it: say what the source does establish instead of rounding it up to what you expected. And when a page carries a canonical list (permissions, prerequisites, ordered steps), read the whole section by range rather than grepping for the items you expect, since a grep built from your expectation can only ever confirm it.

**Load the `web-fetch` skill** when a fetch fails, is refused or comes back as boilerplate, when exact text from a page matters, and before fetching Reddit, a bot-protected or paywalled site, or anything through `agent-chromium`. It has the escalation ladder (`jina-fetch --proxy`, then `agent-chromium`, the user's logged-in Chromium), the failure signatures, and how to quote from the cached page. `agent-chromium` is the user's real account: read only, and never attempt a CAPTCHA, type a password or fill a sign-up form.
