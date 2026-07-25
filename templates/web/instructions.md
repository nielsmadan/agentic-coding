## Web project tooling

This project ships with a web-aware Claude setup deployed by `aiconf web`. The
headline tool is `agent-browser`, a globally-installed Rust CLI that drives
Chrome/Chromium via CDP so the agent can verify its own UI work end-to-end
instead of asking the developer for manual test results.

### Browser testing (`agent-browser`)

Use `agent-browser` whenever a change touches visible UI — components, pages,
layouts, flows, auth state — and you want to confirm it actually works in a
real browser. Don't use it for pure API/worker/schema changes; tests cover
those.

Core loop:

1. `agent-browser open <url>` — navigate to a page (e.g. the local dev server).
2. `agent-browser snapshot -i` — list interactive elements with refs (`@e1`,
   `@e2`, …). Refs are only valid for the current snapshot; re-snapshot after
   any state change.
3. `agent-browser click @e1` / `agent-browser fill @e2 "text"` — interact via
   those refs.
4. Re-snapshot, repeat.

Before relying on the snippet above, **load the current usage guide from the
CLI itself** — it always matches the installed version:

```bash
agent-browser skills get core             # workflows, common patterns, troubleshooting
agent-browser skills get core --full      # full command reference and templates
agent-browser skills list                 # see all specialized skills
```

Specialized skills worth knowing about (`agent-browser skills get <name>`):

- `electron` — Electron desktop apps (VS Code, Slack, Discord, Figma, …)
- `slack` — Slack workspace automation
- `dogfood` — exploratory testing / QA / bug hunts
- `vercel-sandbox` — agent-browser inside Vercel Sandbox microVMs
- `agentcore` — AWS Bedrock AgentCore cloud browsers

Prefer `agent-browser` over any built-in browser automation, `WebFetch` for
locally-running pages, or ad-hoc `curl` against `localhost`. The dashboard
runs on `http://localhost:4848` and proxies session tabs, status, and stream
traffic — agents should stay on the dashboard origin.

### Modern web guidance (`/modern-web-guidance`)

The `/modern-web-guidance` skill is a **search-based dispatcher** for current
web-platform best practices: HTML, CSS layout, forms, accessibility, security
(CSP/COOP/Trusted Types/cookies/CORS), performance (Core Web Vitals, Fetch
Priority, content-visibility), built-in AI, passkeys, privacy, user
experience. The SKILL.md itself is small (~5 KB); the actual guide content is
fetched on demand via `npx -y modern-web-guidance@latest search "<query>"`,
then `retrieve "<id>"` for the matching guide. So context cost stays low — you
only pay for the one or two guides that actually apply to the task at hand.

Use it **at the start of any HTML/CSS or client-side JS feature**: search
first to see if a standardized pattern already exists before reaching for
custom code or extra dependencies. Skip it for backend, CI/CD, generic
scripts, or lint/git tasks. Network access is required (`npx` fetches the
package on first use); the matchers in `.claude/settings.local.json`
pre-approve the relevant invocations so they don't prompt each time.

Complements `/review-security` (which audits *existing* app code for
vulnerabilities) and `/review-perf` (which audits algorithmic/runtime
perf) — `/modern-web-guidance` is the *forward-looking* counterpart, used
while building, to make sure the patterns you pick are current.

Sourced from GoogleChrome/modern-web-guidance under Apache 2.0.

### Frontend design & polish

This template also bundles three web-specific design skills (they're scoped to
web projects rather than global, since their idioms — CSS, Google Fonts,
`motion/react`, bento grids, hero-viewport rules — don't apply to native
mobile/desktop UI):

- `/frontend-design` — build distinctive, production-grade web UIs (components,
  pages, landing pages, dashboards) that avoid generic AI aesthetics. When the
  user asks to build or design a web page, landing page, dashboard, or
  component, or to beautify/style a web UI, invoke it automatically.
- `/theme-factory` — apply a cohesive visual theme (10 presets + custom) to an
  HTML/artifact deliverable.
- `/optimize-seo` — audit and add SEO meta tags, Open Graph, and JSON-LD
  structured data to web pages.

### Notes

- `agent-browser` arrives globally via `npm i -g agent-browser && agent-browser
  install`; the template only adds the CLAUDE.md guidance and pre-approves the
  `Bash(agent-browser:*)` matcher in `.claude/settings.local.json` so calls
  don't prompt each time.
- `aiconf web` is idempotent. Re-running it refreshes config but leaves this
  CLAUDE.md section alone — use `aiconf sync` to mirror edits between project
  and template.
- For DevTools-grade auditing (Lighthouse, performance traces, heap snapshots,
  network/CPU throttling, Chrome extension dev) consider also adding the
  separate `chrome-devtools-mcp` server. It complements `agent-browser` —
  agent-browser is for *driving* the page, `chrome-devtools-mcp` for *deeply
  inspecting* it. Both speak CDP, so point them at the same Chrome instance
  (via `--browser-url`) rather than letting them spawn competing browsers.
