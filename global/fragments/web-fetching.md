## Web Fetching

External URLs are best fetched through the Jina MCP server, which renders JS server-side and returns clean markdown — avoiding the HTML-skeleton problem `WebFetch` has on SPAs.

**Default**: use `mcp__jina__read_url` (or `mcp__jina__parallel_read_url` for multiple URLs) for external pages.

**Use plain `WebFetch` for**:
- `github.com` URLs (repo pages, issues, PRs, raw files) — already return sensible HTML
- Local dev servers (`localhost`, `127.0.0.1`)
- Plain HTML/RSS/Atom/PDF where the Jina detour adds latency without value

**Fall back to `WebFetch`** if the Jina MCP is unavailable (key missing, rate-limited, server down) or returns thin content.

**Authenticated or anti-bot sites** are not supported via either path — use `gh`, `glab`, or project-specific CLIs instead.

**Auth**: the Jina MCP's auth happens automatically — token comes from the SOPS-encrypted store via the `claude` zsh wrapper, interpolated into the request header by Claude Code at startup. The agent does not need to know or fetch the value (see Secrets below).