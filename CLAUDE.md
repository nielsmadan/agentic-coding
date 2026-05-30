# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This repository contains shared configuration for agentic coding tools. It includes skills, hooks, and permission settings that can be used across multiple projects.

## Structure

- `claude/` - Claude Code specific configuration
  - `settings.json` - Permissions, hooks, and status line config (the `permissions.*` arrays are **generated** — see Permissions below)
  - `skills/` - Custom skills in `<skill-name>/SKILL.md` format
  - `hooks/` - Shell scripts triggered by events (e.g., notification when waiting for input)
- `codex/` - OpenAI Codex CLI configuration
  - `rules/` - Permission rules (**generated** — see Permissions below)
  - `skills/` - Codex-specific overrides; `install.sh` syncs the curated subset of `claude/skills/` to `~/.agents/skills/`
- `permissions/` - Single source of truth for agent shell-command permissions
  - `permissions.toml` - the source; edit this
  - `sync.py` - regenerates every agent's permission config from the source
- `templates/` - Project-type config + skills deployed per-project (see Project Templates below)
  - `<type>/` - config fragments and project-only skills for a project type (e.g. `flutter/`)
    - `.mcp.json`, `settings.local.json` - merged into the target project
    - `skills/<name>/` - project-only skills, copied into the target's `.claude/skills/`
    - `claude-md.md` *(optional)* - markdown snippet appended once to the project's
      `CLAUDE.md` on first install; updates flow through `aiconf sync` afterwards
  - `deploy.py` - copies/merges a type's contents into a target project
- `.airc` - entry point sourced from `~/.zshrc` (symlinked from `~/.airc`); loads everything under `.airc.d/`
- `.airc.d/` - one `.zsh` file per topic, sourced in glob order
  - `00-path.zsh` puts `bin/` on PATH; `10-env.zsh` sets shared env vars; the rest hold aliases/functions per tool
- `bin/` - standalone CLI scripts on PATH (e.g. `ccmove`, `clcof`); add new ones here rather than as zsh functions

## Shell Config

Add a new alias or shell function: drop it in the appropriate `.airc.d/<topic>.zsh`, or create a new topic file. Reload with `source ~/.airc` (idempotent — re-sourcing does not duplicate PATH entries).

Add a new CLI command with flags, validation, or non-trivial logic: write it as a Python script under `bin/<name>` (no extension) with `#!/usr/bin/env python3` and `chmod +x`. It becomes available on PATH automatically. Keep zsh wrappers only when shell-specific behavior is needed (e.g. `print -z` to put text on the zle buffer, backgrounding with `& disown`).

## Skills

Available in `claude/skills/`:

| Skill | Purpose |
|-------|---------|
| `/code-review` | Code review workflow |
| `/frontend-design` | Build distinctive frontend interfaces with high design quality |
| `/debug-log` | Add debug logging to trace code execution |
| `/hard-fix` | Escalation workflow for stubborn bugs |
| `/perf-test` | Set up and run performance tests with improvement cycle |
| `/review-plan` | Multi-agent review of implementation plans |
| `/review-product` | Review a product from the user's perspective — build a persona, map use cases, audit friction/gaps (`--live`, `--multi`); writes to `docs/product/`, checks it against `docs/prd/` |
| `/read-docs` | Search internal project documentation (proactive) |
| `/research-code` | Research a programming topic online using parallel agents |
| `/research-general` | Research a non-programming topic online (academic, news, primary sources, fact-checks) using parallel agents |
| `/resolve-conflicts` | Git merge conflict resolution |
| `/sync-project-config` | Bidirectional sync of project config (`.mcp.json`, bundled skills) with its template (invoked by `aiconf sync`) |
| `/summary` | Explain staged git changes in detail and propose conventional-commit messages. `--quick` for a recap of the current task and next steps |
| `/review-history` | Analyze git history and past issue logs |
| `/review-comments` | Review and clean up low-quality code comments (--all, --staged, --changed) |
| `/review-perf` | Performance analysis (--staged, --all) |
| `/review-interfaces` | Interface design review for functions, classes, components (--staged, --all) |
| `/review-architecture` | System architecture review — layering, module boundaries, coupling, pattern fit, quality attributes (--staged, --all, --multi) |
| `/review-cleancode` | Clean code principles review - SOLID, DRY, YAGNI, KISS, code smells (--staged, --all, --multi) |
| `/review-security` | Security audit for vulnerabilities (--staged, --all) |
| `/doc` | Documentation review, update, and generation (--review, --update, --generate) |
| `/explain` | Generate project explanation docs in `docs/explain/` (--architecture, --flows, --syntax, --system, --infra, --test, --all, --staged, optional topic filter) |
| `/test` | Test review and generation (--review, --generate) |
| `/theme-factory` | Apply professional visual themes to artifacts (presentations, docs, HTML) |
| `/todo` | Capture a todo in Todoist (--prio 1-4, --list) |
| `/pre-existing` | Force a rigorous investigation of "pre-existing" test/lint/type/CI failures instead of dismissing them |
| `/pdf` | PDF processing: read, merge, split, create, fill forms, OCR |
| `/second-opinion` | Get a second opinion |
| `/review-logs` | Analyze session transcripts for failure patterns and suggest fixes |
| `/optimize-seo` | Audit and optimize web pages for SEO (meta tags, structured data, OG tags) |
| `/skill-creator` | Guide for creating skills |
| `/temp` | Make temporary code changes for testing, easily undone with `/temp undo` |

## Claude Desktop Skills

Skills under `claude/desktop/skills/` are deployed to Claude Desktop manually:
1. Edit `claude/desktop/skills/<name>/SKILL.md` (and any `references/`)
2. Run `./claude/desktop/package-skills.sh` — produces `claude/desktop/zips/<name>.zip`
3. Upload the zip via Claude Desktop's UI (no automation)

The unpacked copies in `~/Library/Application Support/Claude/local-agent-mode-sessions/skills-plugin/...` are read-only — never edit there.

## Permissions

Shell-command permissions for all four agents (Claude, Codex, Antigravity, OpenCode) are generated from a single source of truth: **`permissions/permissions.toml`**.

**Never hand-edit these generated files** — a lefthook pre-commit hook (`sync.py --check`) rejects any drift:
- `claude/settings.json` (`permissions.allow` / `deny` / `ask`)
- `codex/rules/permissions.rules`
- `antigravity/settings.json` (`permissions.allow` / `deny` / `ask`)
- `opencode/opencode.json` (`permission.bash`)

To change permissions: edit `permissions/permissions.toml`, then run `python3 permissions/sync.py` (also run automatically by `install.sh`). `[shell]` entries (allow/deny/ask) go to all four agents; `[claude.extra]` / `[opencode.extra]` hold tool-native entries (`Skill()`, `mcp__*`, OpenCode toggles) with no cross-agent equivalent. Codex's token matcher can't express glob entries (those ending in `*`), so they fall through to its normal approval prompt.

## Project Templates

`templates/<type>/` holds config and skills that belong to a *kind* of project rather than to
every session. For example `templates/flutter/` carries the Flutter MCP servers (`.mcp.json`),
their enablement + `mcp__*` permissions (`settings.local.json`), and project-only skills like
`flutter-upgrade` (`skills/<name>/`). Keeping it here version-controls the config centrally
without making it global: a project-root `.mcp.json` is project-scoped (only loads inside that
project), and a skill bundled with a template only shows up after deployment — it never
pollutes Claude sessions in unrelated projects.

Two CLI verbs (defined in `.airc`):

```
aiconf <type> [dir]   # mechanical install: deploy template into dir (default cwd)
aiconf sync           # from a project dir: bidirectional sync against its template
aiconf sync <dir>     # from ~/ac: bidirectional sync against <dir>
```

**Install** (`aiconf <type> [dir]`) runs `templates/deploy.py`. It **copies** (not symlinks)
so the target project owns real, committable files. Each step is idempotent in its own way:
- `.mcp.json` and `settings.local.json` merge (union arrays, preserve unrelated entries).
  `.mcp.json` is read by all four agents at project root; `settings.local.json` stays
  Claude-scoped at `.claude/settings.local.json`
- `skills/<name>/` recursively copy into `<target>/.claude/skills/<name>/`, only writing files
  whose bytes differ. A `.agents/skills/<name>` symlink is added pointing back at the
  Claude copy, so Codex / Gemini CLI / Antigravity pick up the same project skills
- `instructions.md` (optional) is **appended once each** to `<target>/CLAUDE.md` and
  `<target>/AGENTS.md` on first install for a given type. State is tracked per (type,
  target-file) pair in `<target>/.aiconf/state.json` so subsequent installs skip files that
  already received the append (and can backfill a missing one). After install, the snippet is
  yours — refactor, integrate, move it freely; use `aiconf sync` to mirror edits between
  project and template.

Add `.aiconf/` to a project's `.gitignore` (alongside `.claude/settings.local.json`) — it's
machine-local install state.

To update template-side fragments, edit `templates/<type>/` and re-deploy (for the mechanical
artifacts) or use `aiconf sync` (for the instructions snippet, since install doesn't touch
the CLAUDE.md / AGENTS.md passages after first run).

**Sync** (`aiconf sync [dir]`) opens an interactive Claude session that invokes the
`/sync-project-config` skill. The skill picks per-file direction (pull project→template or
push template→project) from `diff` + `git log` / `git status`, scoped to artifacts already
defined in the template. CLAUDE.md and AGENTS.md are synced as independent targets — a pull
from one does not auto-overwrite the other. `settings.local.json` is intentionally out of
scope for sync — recommend `aiconf <type> <dir>` for mechanical settings refresh.

Project-only skills live *inside* their template (`templates/<type>/skills/<name>/`), not in
`claude/skills/`, so `install.sh` never exposes them globally. To turn an existing global skill
into a project-only one, move its directory from `claude/skills/<name>/` to
`templates/<type>/skills/<name>/`.

Templates cover config only; machine prerequisites (e.g. `npx`, `uvx`, `dart` for the Flutter
MCP servers) must be installed separately.

### Considered but not bundled

- **`chrome-devtools-mcp`** (Chrome DevTools for Agents v1, May 2026) — Chrome team's MCP
  server with Lighthouse audits, performance traces, heap snapshots, network/CPU throttling,
  Chrome extension dev, WebMCP debugging. Complements the `web` template's `agent-browser`
  (driving the page) with DevTools-grade *inspection* of the page. Not bundled by default
  because most web projects don't need it day-to-day and both speak CDP — running both
  against the same Chrome requires pointing chrome-devtools-mcp at agent-browser's instance
  via `--browser-url`, which is fiddly enough to opt into per-project. Install as a Claude
  Code plugin: `/plugin install chrome-devtools-mcp@chrome-devtools-plugins` after
  `/plugin marketplace add ChromeDevTools/chrome-devtools-mcp`.

## Secrets Policy

**Never commit API tokens, secrets, or credentials to any file in this repo.** This repo is version-controlled and shared. MCP server configs use `${ENV_VAR}` interpolation for auth — never hardcode tokens.

Dev secrets are SOPS-encrypted and injected into subprocesses by zsh wrappers around the AI CLI tools. Do not enumerate, read, or echo the secrets store from this session — see `~/.claude/CLAUDE.md` "Secrets" for the agent-facing rules.

## Git Policy

Leave git to the user. Do not run git commands that modify state (`add`, `commit`, `checkout`, `branch`, `merge`, `rebase`, `stash`, etc.) unless the user explicitly asks for that specific operation. A few commands are hard-blocked at the harness level — `git push`, `git branch -d/-D`, `git reset --hard`, `git clean -f*` — because they push to a remote or destroy local work; ask the user to run those manually.

Read-only inspection (`status`, `log`, `diff`, `show`, `branch` listing, etc.) is always fine.

## GitHub Commands

Prefer dedicated `gh` subcommands over `gh api`:
- Issue comments: `gh issue view <num> --comments -R <owner/repo>`
- PR comments: `gh pr view <num> --comments -R <owner/repo>`
- PR reviews: `gh pr view <num> --json reviews -R <owner/repo>`
- Releases: `gh release list -R <owner/repo>`
- Workflow runs: `gh run list -R <owner/repo>`

Do NOT use `gh api` when a dedicated subcommand exists.

## Verification Policy

Never claim "best practice", "recommended", "accepted solution", "community consensus", "known bug", "known issue", or "known limitation" without a cited source. If you haven't verified something, say "I believe" or "this might work" - not "this is the way."

**Do NOT say:**
- "This is the accepted approach" → without a source, you don't know this
- "The community recommends" → find a citation or don't claim consensus
- "This is best practice" → according to whom?
- "Known bug" / "known issue" → known by whom? Link the issue or say "I suspect"

When unsure, be explicit: "I think this will work, but I haven't verified it's the recommended approach."

## Test & Lint Failures

Never dismiss test failures, linting errors, or type errors as "pre-existing issues." Fix them. All repos use pre-commit hooks that enforce clean tests and linting — if something fails after your changes, either your changes caused it or it needs fixing regardless. Do not:
- Skip failing tests by claiming they were already broken
- Suggest the user "ignore" lint errors
- Offer to "move on" without fixing failures
- Acknowledge a failure is "pre-existing" and then stop — that is not fixing it
- Use `git diff` to prove something isn't your fault as justification for leaving it broken

"Fix it" means the check passes. The only acceptable outcome is ALL checks green. If a failure is genuinely unrelated to your changes, fix it anyway (and note it was pre-existing).

## Fix Escalation

When fixing a bug or error, track how many fix attempts have failed (a failed attempt = you made a change, re-ran the check, and it still fails):
- **After 2 failed fixes:** Automatically invoke `/second-opinion` to get external perspective before trying again.
- **After 4 failed fixes:** Automatically invoke `/hard-fix` to switch to the structured escalation workflow.

Do not keep trying the same approach. Each escalation tier forces a fresh perspective.

## Build & Check Workflow

- After writing or creating any new file, run the project's formatter before running check-all or lint commands.
- When a typecheck or lint command fails, read ALL errors and fix them in one pass before re-running. Do not fix one error and re-check.
- When moving or renaming files: update imports, barrel/index exports, and clear build caches (e.g., `.next`, `build/`) in the same pass — before re-running checks.
- When changing a shared type or component prop, grep for all consumers and update them before re-running typecheck.
- Do not reflexively re-run a failing command without making changes first. If it failed, something needs fixing.

## Keyword Triggers

When the user's prompt contains "second opinion", automatically invoke the `/second-opinion` skill to get external advisor input.

When the user's prompt contains "research online", automatically invoke whichever skill fits the topic: `/research-code` for programming, library docs, code patterns, error debugging, or version-specific issues; `/research-general` for non-programming topics — academic, historical, current events, regional/regulatory, consumer, fact-checking. If the topic is genuinely ambiguous, default to `/research-general`.

When the user's prompt contains "review plan", "review the plan", or "review my plan", automatically invoke the `/review-plan` skill to get multi-agent feedback before implementation.

When the user's prompt contains "add debug logs" or "debug logging", automatically invoke the `/debug-log` skill to instrument code with tracing.

When the user's prompt contains "review history" or "git history" or "how did this change", automatically invoke the `/review-history` skill to analyze code evolution.

When the user's prompt mentions `.pdf` files or asks to work with PDFs (merge, split, extract text, create, fill forms, OCR, watermark), automatically invoke the `/pdf` skill.

When the user's prompt asks to build or design a web page, landing page, dashboard, or component, or to beautify/style a web UI, automatically invoke the `/frontend-design` skill.

When the user's prompt contains "review logs", "session analysis", or "failure patterns", automatically invoke the `/review-logs` skill to analyze session transcripts.

When the user's prompt contains "pre-existing", "preexisting", "already broken", or "flaky test", or when you are about to label a test/lint/type/build/CI failure as pre-existing, unrelated, or not your fault, automatically invoke the `/pre-existing` skill before stopping.

## Internal Documentation

When a `docs/` folder exists, proactively check internal documentation using `/read-docs`:

**Automatic triggers:**
- Before planning a new feature or significant change
- When entering a new area of the codebase for the first time
- When debugging issues (check for documented gotchas)
- When the user asks about conventions, patterns, or architecture

This supplements CLAUDE.md with detailed project-specific knowledge. For external library docs, use `/research-code` instead.
