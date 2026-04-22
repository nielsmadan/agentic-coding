# Global CLAUDE.md

User-scoped guidance that applies to every Claude Code session on this machine. Loaded from `~/.claude/CLAUDE.md` (symlinked to this file).

Keep this file **project-agnostic** — anything specific to a particular repo belongs in that repo's own `CLAUDE.md`.

## Web Fetching

External URLs are best fetched through the Jina MCP server, which renders JS server-side and returns clean markdown — avoiding the HTML-skeleton problem `WebFetch` has on SPAs.

**Default**: use `mcp__jina__read_url` (or `mcp__jina__parallel_read_url` for multiple URLs) for external pages.

**Use plain `WebFetch` for**:
- `github.com` URLs (repo pages, issues, PRs, raw files) — already return sensible HTML
- Local dev servers (`localhost`, `127.0.0.1`)
- Plain HTML/RSS/Atom/PDF where the Jina detour adds latency without value

**Fall back to `WebFetch`** if the Jina MCP is unavailable (key missing, rate-limited, server down) or returns thin content.

**Authenticated or anti-bot sites** are not supported via either path — use `gh`, `glab`, or project-specific CLIs instead.

**Key management**: the API key lives in `$JINA_API_KEY` in the user's shell, and `~/.claude.json` references it as `${JINA_API_KEY}`. Never commit the raw key.
