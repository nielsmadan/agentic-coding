## Web Fetching

For fetching and searching external web content, prefer the **Jina MCP tools** (configured for this agent): they render JavaScript server-side and return clean markdown, avoiding the HTML-skeleton problem a plain fetch hits on SPAs.

**Default**: use the Jina MCP `read_url` tool for external pages and its web-search tool for queries. The exact tool name depends on the agent's MCP integration — e.g. in Pi the Jina tools are reached through the MCP adapter's proxy; in Codex/Antigravity they surface as `jina` server tools.

**Skip Jina — use `curl` or your built-in fetch directly — for**:
- `github.com` URLs (repo pages, issues, PRs, raw files) — already return sensible HTML/JSON
- Local dev servers (`localhost`, `127.0.0.1`)
- Plain HTML/RSS/Atom/PDF where the Jina detour adds latency without value

**Fall back to a plain fetch** if the Jina MCP is unavailable (not configured, rate-limited, server down) or returns thin content.

**Authenticated or anti-bot sites** are not supported via either path — use `gh`, `glab`, or project-specific CLIs instead.

**Auth** is injected automatically by the sops-wrapped launcher; you do not need to know or fetch the token (see Secrets).
