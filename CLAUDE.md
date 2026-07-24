# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This repository contains shared configuration for agentic coding tools. It includes skills, hooks, and permission settings that can be used across multiple projects.

## Structure

- `claude/` - Claude Code specific configuration
  - `settings.json` - Permissions, hooks, and status line config (the `permissions.*` arrays are **generated** — see Permissions below)
  - `CLAUDE.md`, `CLAUDE.autonomous.md` - global Claude guidance (**generated** — see Global Instructions below)
  - `skills/` - Custom skills in `<skill-name>/SKILL.md` format
  - `hooks/` - Shell scripts triggered by events (e.g., notification when waiting for input)
- `codex/` - OpenAI Codex CLI configuration
  - `rules/` - Permission rules (**generated** — see Permissions below)
  - `skills/` - Codex-specific overrides; `install.sh` syncs the curated subset of `claude/skills/` to `~/.agents/skills/`
- `antigravity/` - Antigravity (`agy`) configuration
  - `settings.json` - permissions.* arrays are **generated** (rest editable)
- `pi/` - Pi (`pi-coding-agent`) configuration
  - `settings.json` - symlinked to `~/.pi/agent/settings.json`; holds the `enabledModels`
    allowlist that scopes the model picker (see Pi below). Pi reads global instructions from
    `~/.pi/agent/AGENTS.md` (the shared `global/AGENTS.md`) and auto-discovers skills from
    `~/.agents/skills/`, so those need no pi-specific files. Pi has no shell-permission system,
    so it is **not** part of `permissions/sync.py`.
- `permissions/` - Single source of truth for agent shell-command permissions
  - `permissions.toml` - the source; edit this
  - `sync.py` - regenerates every agent's permission config from the source
- `global/` - Single source of truth for each agent's **global** (machine-wide) instructions
  - `fragments/` - shared prose sections (browser automation, secrets, git policy, ...); edit these
  - `sync.py` - assembles the fragments into each agent's global instruction file
  - `AGENTS.md` - **generated** shared file for every non-Claude agent (symlinked to `~/.codex/AGENTS.md` + `~/.gemini/GEMINI.md`); see Global Instructions below
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
| `/check-claude-projects` | Search past session transcripts under `~/.claude/projects` (current project + sibling checkouts) to recover prior context — e.g. a bug fixed in an earlier session you can't locate |
| `/check-notes` | Find information in the user's personal Obsidian vault at `~/wrksp/notes` — reads its hand-maintained `index.md` map to locate the topic, falls back to searching the vault |
| `/code-review` | Code review workflow. Runs 9 language-agnostic aspects, plus auto-detected language reviews (`review-<lang>`) and a per-project `review-project` skill when present |
| `/review-typescript` | TypeScript judgment-level review a linter can't do — type modeling (make invalid states unrepresentable), inference-vs-annotation, casts/`any` hiding a modeling problem. Deliberately non-overlapping with typescript-eslint. Auto-invoked by `code-review` on TS projects; extensible pattern for other languages (`review-<lang>`) |
| `/library-docs` | Generate/refresh a per-repo `library-use` reference — official docs + changelog links, pinned versions, and distilled correct-usage conventions for the repo's fast-moving/niche libraries. Re-run version-checks entries: same-API bumps auto-update, API-changing bumps report + draft a migration and ask before applying |
| `/review-library-use` | Reviews code against the repo's `library-use` conventions — stale/renamed APIs, deprecated patterns, missing required setup a general reviewer misses. Auto-invoked by `code-review` when a `library-use` reference exists |
| `/frontend-design` | Build distinctive frontend interfaces with high design quality |
| `/guide` | Walk through a multi-step UI/console task (e.g. cloud permission setup), re-printing a live step tracker at the bottom of every reply so you never scroll up |
| `/debug-log` | Add debug logging to trace code execution |
| `/hard-fix` | Escalation workflow for stubborn bugs |
| `/perf-test` | Set up and run performance tests with improvement cycle |
| `/plan` | Lightweight middle-tier planning — a read-only Fable subagent drafts a concrete plan (approach, file manifest, ordered steps, risks, open questions), you approve at one go-ahead gate, then Opus implements in auto mode. Never enters plan mode (dodges the plan-mode permission prompts). `--review` runs multi-agent `review-plan` before the gate |
| `/review-plan` | Multi-agent review of implementation plans |
| `/breakdown-milestone` | Break a milestone (e.g. M0) into incremental sprints of working software |
| `/breakdown-sprint` | Break a sprint (e.g. s1) into ordered, parallelizable tasks following agile user-story principles |
| `/review-product` | Review a product from the user's perspective — build a persona, map use cases, audit friction/gaps (`--live`, `--multi`); writes to `docs/product/`, checks it against `docs/prd/` |
| `/ideation` | Generate ideas with structure when stumped — on what to build, the real problem, or a solution. Routes frameworks by stuck-state, diverges then converges to a prioritized shortlist (`--problem`, `--feature`, `--solution`, `--quick`) |
| `/read-docs` | Search internal project documentation (proactive) |
| `/cld-md-improver` | Audit and improve CLAUDE.md files (project-memory optimization) |
| `/research-tech` | Research any technical/developer topic online using parallel agents — libraries, errors, best practices, tool/library/model comparisons, product capabilities, ecosystem signal |
| `/research-general` | Research a non-technical topic online (academic, news, primary sources, consumer, fact-checks) using parallel agents |
| `/resolve-conflicts` | Git merge conflict resolution |
| `/commit` | Commit only the changes THIS session made (never another agent's work in a shared checkout) — stages by explicit path, hunk-level when a file is co-edited. Optional message arg; generates a short feat/fix/chore message when blank |
| `/squash-commits` | Squash unpushed commits into clean higher-level feat/fix/chore commits per the commit policy (`--conservative`, optional base ref) |
| `/sync-project-config` | Bidirectional sync of project config (`.mcp.json`, bundled skills) with its template (invoked by `aiconf sync`) |
| `/summary` | Explain staged git changes in detail and propose conventional-commit messages. `--quick` for a recap of the current task and next steps |
| `/review-history` | Analyze git history and past issue logs |
| `/review-comments` | Review and clean up low-quality code comments (--all, --staged, --changed) |
| `/deslop` | Copy-edit text to strip AI/LLM writing tells (overused words, significance-inflation phrases, scene-setting openers, em-dash overuse, rule-of-three, "it's not X, it's Y"); `--report` to flag without rewriting |
| `/review-perf` | Performance analysis (--staged, --all) |
| `/review-interfaces` | Interface design review for functions, classes, components (--staged, --all) |
| `/review-architecture` | System architecture review — layering, module boundaries, coupling, pattern fit, quality attributes (--staged, --all, --multi) |
| `/review-cleancode` | Clean code principles review - SOLID, DRY, YAGNI, KISS, code smells (--staged, --all, --multi) |
| `/review-security` | Security audit for vulnerabilities (--staged, --all) |
| `/doc` | Documentation: assess state and run the right action (default, no args — surveys gaps/staleness/quality and routes), or explicit review/update/generate/session (--review, --update, --generate, --session) |
| `/explain` | Generate project explanation docs in `docs/explain/` (--architecture, --flows, --syntax, --system, --infra, --test, --all, --staged, optional topic filter) |
| `/test` | Tests: assess state and run the right action (default, no args — runs the suite, then routes failures to fix, gaps to generate, smells to review), or explicit review/generate (--review, --generate) |
| `/theme-factory` | Apply professional visual themes to artifacts (presentations, docs, HTML) |
| `/todo` | Capture a todo in Todoist (--prio 1-4, --list) |
| `/time-reconstruct` | Reconstruct what you worked on from git history for time tracking — real complexity assessment from the diff, not its size |
| `/pre-existing` | Force a rigorous investigation of "pre-existing" test/lint/type/CI failures instead of dismissing them |
| `/pdf` | PDF processing: read, merge, split, create, fill forms, OCR |
| `/second-opinion` | Get a second opinion |
| `/review-logs` | Analyze session transcripts for failure patterns and suggest fixes |
| `/optimize-seo` | Audit and optimize web pages for SEO (meta tags, structured data, OG tags) |
| `/use-railway` | Operate Railway infrastructure — accounts, projects, services, deployments, buckets, domains, metrics, docs |
| `/skill-creator` | Guide for creating skills |
| `/temp` | Make temporary code changes for testing, easily undone with `/temp undo` |

### Extending code-review per language / per project

`code-review` layers four tiers of checks:

1. **9 language-agnostic aspects** — always run (logic, architecture, security, …).
2. **Language reviews** — global skills named `review-<language>` in `claude/skills/`. Auto-invoked when `code-review` detects that language in the scoped files. `review-typescript` is the first. Add a new language by creating `review-<language>/SKILL.md` and adding a row to the detection registry in `code-review`'s Step 3b.5.
3. **Project review** — an *individual project* can define `.claude/skills/review-project/SKILL.md` for checks unique to that codebase. `code-review` calls it only when it exists; projects without one are unaffected. The minimal shape is documented in `code-review`'s "Language & project reviews" section.
4. **Library-use review** — global `review-library-use` checks code against a per-repo `library-use` reference (docs-derived, version-specific correct-usage conventions). Auto-invoked when the repo has `.claude/skills/library-use/SKILL.md`, which the global `library-docs` skill generates and refreshes. Trio: `library-docs` (build/refresh) → `library-use` (per-repo reference) → `review-library-use` (audit).

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
- `claude/settings.autonomous.json` (autonomous-dev profile — see below)
- `codex/rules/permissions.rules`
- `antigravity/settings.json` (`permissions.allow` / `deny` / `ask`)
- `opencode/opencode.json` (`permission.bash`)

To change permissions: edit `permissions/permissions.toml`, then run `python3 permissions/sync.py` (also run automatically by `install.sh`). `[shell]` entries (allow/deny/ask) go to all four agents; `[claude.extra]` / `[opencode.extra]` hold tool-native entries (`Skill()`, `mcp__*`, OpenCode toggles) with no cross-agent equivalent. Codex's token matcher can't express glob entries (those ending in `*`), so they fall through to its normal approval prompt.

### Autonomous-dev profile

For machines that run autonomous dev tasks (which must `git push` etc. without a human in the loop) there is a second **Claude-only** profile built around auto mode's classifier. `sync.py` always generates both `claude/settings.json` and `claude/settings.autonomous.json`; the autonomous variant keeps `defaultMode: "auto"` but **empties `allow` / `deny` / `ask`** so the classifier judges every tool call. Clearing `deny` is what lets `git push` and the other destructive-git ops through (deny overrides every mode, including auto); the `allow` / `ask` lists are dropped so nothing pre-empts or blocks the classifier (an `ask` would also hang a headless run). `claude/CLAUDE.autonomous.md` is the matching global-guidance variant whose Git Policy permits autonomous git ops. Both `claude/CLAUDE.md` and `claude/CLAUDE.autonomous.md` are **generated** from shared fragments (see Global Instructions below), so they never drift — the autonomous variant differs only by pulling the `git-policy.autonomous` fragment instead of `git-policy`.

Install the autonomous profile with `./install.sh --autonomous`, which symlinks the `*.autonomous` variants to `~/.claude/settings.json` and `~/.claude/CLAUDE.md` instead of the defaults. Plain `./install.sh` installs the normal profile. The other three agents (Codex, Antigravity, OpenCode) get the same config under either profile.

## Global Instructions

Each agent's **global** (machine-wide) natural-language guidance — browser automation, secrets handling, git policy, etc. — is generated from a single source of truth: the fragments in **`global/fragments/`**. `global/sync.py` assembles them into each agent's global instruction file, the same generate-and-check pattern used for permissions.

**Never hand-edit these generated files** — a lefthook pre-commit hook (`global/sync.py --check`) rejects any drift:
- `claude/CLAUDE.md` and `claude/CLAUDE.autonomous.md` → symlinked to `~/.claude/CLAUDE.md`
- `global/AGENTS.md` → symlinked to **both** `~/.codex/AGENTS.md` (Codex) and `~/.gemini/GEMINI.md` (Antigravity's `agy`)

**Only Claude gets its own file.** It needs the `CLAUDE.md` filename, the Jina Web Fetching section, and the autonomous git-policy variant. Every other agent shares one `global/AGENTS.md` — the content is identical, so there's no reason to branch per-agent until one actually needs something different. (Codex reads global instructions from `~/.codex/AGENTS.md`, `agy` from `~/.gemini/GEMINI.md`; the destinations differ but point at the same source.)

To change global guidance: edit a fragment in `global/fragments/`, then run `python3 global/sync.py` (also run automatically by `install.sh`). Each target's fragment list lives in `TARGETS` in `sync.py`, so the differences that exist are explicit — e.g. `web-fetching` (the Jina MCP) is Claude-only because only Claude has that MCP configured; the autonomous profile swaps in the `git-policy.autonomous` fragment.

**Why a generator, not native `@imports`:** only Claude Code and Gemini CLI expand in-file `@path` imports; Codex and OpenCode have no import mechanism, and Antigravity's `agy` (a closed-source rewrite) is unverified. A generator is the only DRY approach that works uniformly across every agent.

**OpenCode** gets no file of its own: it reads `~/.claude/CLAUDE.md` as a global-rules fallback. Per OpenCode's docs it treats that file as plain rules and does not expand `@imports` — moot here, since the generated file is already fully expanded. Disable via `OPENCODE_DISABLE_CLAUDE_CODE_PROMPT=1` if ever unwanted.

## Pi

Pi (`@earendil-works/pi-coding-agent`, installed via mise) is wired up like the other non-Claude
harnesses, but through Pi's own mechanisms rather than the generated permission/global pipelines:

- **Global instructions** — Pi loads `~/.pi/agent/AGENTS.md`, symlinked to the shared
  `global/AGENTS.md` (same file as Codex/Antigravity).
- **Skills** — Pi auto-discovers `~/.agents/skills/` (and `~/.pi/agent/skills/`) by default. That
  first directory is already populated by `install_codex_skills`, so Pi gets the same curated skill
  subset as Codex/Antigravity with no pi-specific config. Skills surface as `/skill:<name>` and via
  progressive disclosure in the system prompt.
- **Permissions** — Pi has **no** shell-command allowlist or sandbox (only a project-*trust* guard
  for loading project-local resources). There is nothing for `permissions/sync.py` to generate, so
  Pi is intentionally absent from `permissions/permissions.toml`.
- **Model picker** — `pi/settings.json` (symlinked to `~/.pi/agent/settings.json`) sets
  `enabledModels`, a glob allowlist (`provider/id`, minimatch, same format as Pi's `--models` flag)
  that scopes the `/model` default view and Ctrl+P cycling. It does **not** delete models from the
  "show all" tab. To change which models are offered, edit the `enabledModels` array. **Do not** edit
  `~/.pi/agent/models-store.json` — that is a fetched catalog cache Pi overwrites on `pi update`.
  Current scope: the GPT-5.6 Codex ladder (`gpt-5.6-luna`/`-terra`/`-sol`, default `-terra`) plus a
  curated openrouter spread (`z-ai/glm-5.2`, `minimax/minimax-m2.5`, `deepseek/deepseek-v4-flash`,
  `qwen/qwen3-coder-next`, `qwen/qwen3-coder:free`).

Unlike the other harnesses' settings files, `pi/settings.json` is runtime-mutable: Pi writes
`lastChangelogVersion` (on upgrades) and any `/settings` / `/model` changes back through the symlink
into the repo file, so expect the occasional small diff to commit or discard.

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

When the user's prompt contains "research online", automatically invoke whichever skill fits the topic. Route by *what you'll do with the answer*, not just subject: `/research-tech` when you'll act on it as a developer — libraries, errors, code patterns, best practices, version issues, **and choosing/evaluating dev tools, models, services, or product capabilities** (even when a product is named); `/research-general` for non-technical topics — academic, historical, current events, regional/regulatory, consumer purchases, personal decisions, fact-checking. Rule of thumb: implement/debug/build-with → `/research-tech`; learn-about/decide/verify a non-code topic → `/research-general`. In a non-code repo (e.g. a notes vault), default research to `/research-general`. If genuinely ambiguous, default to `/research-general`.

When the user's prompt contains "review plan", "review the plan", or "review my plan", automatically invoke the `/review-plan` skill to get multi-agent feedback before implementation.

When the user's prompt contains "ideation", automatically invoke the `/ideation` skill to generate structured ideas.

When the user's prompt contains "add debug logs" or "debug logging", automatically invoke the `/debug-log` skill to instrument code with tracing.

When the user's prompt contains "review history" or "git history" or "how did this change", automatically invoke the `/review-history` skill to analyze code evolution.

When the user's prompt mentions `.pdf` files or asks to work with PDFs (merge, split, extract text, create, fill forms, OCR, watermark), automatically invoke the `/pdf` skill.

When the user's prompt asks to build or design a web page, landing page, dashboard, or component, or to beautify/style a web UI, automatically invoke the `/frontend-design` skill.

When the user's prompt contains "review logs", "session analysis", or "failure patterns", automatically invoke the `/review-logs` skill to analyze session transcripts.

When the user's prompt contains "look through claude projects", "check claude projects", "search past sessions", "search past transcripts", or "find the session where", or otherwise asks to recover context from a previous session whose location is unknown ("we fixed/discussed this before", "which checkout was that in"), automatically invoke the `/check-claude-projects` skill to search `~/.claude/projects`.

When the user's prompt contains "pre-existing", "preexisting", "already broken", or "flaky test", or when you are about to label a test/lint/type/build/CI failure as pre-existing, unrelated, or not your fault, automatically invoke the `/pre-existing` skill before stopping.

## Internal Documentation

When a `docs/` folder exists, proactively check internal documentation using `/read-docs`:

**Automatic triggers:**
- Before planning a new feature or significant change
- When entering a new area of the codebase for the first time
- When debugging issues (check for documented gotchas)
- When the user asks about conventions, patterns, or architecture

This supplements CLAUDE.md with detailed project-specific knowledge. For external library docs, use `/research-tech` instead.
