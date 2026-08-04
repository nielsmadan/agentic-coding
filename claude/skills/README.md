# Skills

Skills extend Claude Code with specialized workflows and capabilities. Invoke them with `/<skill-name>` followed by any arguments.

This file is for humans. Agents get each skill's `description:` frontmatter
injected automatically, so neither `AGENTS.md` nor `CLAUDE.md` restates the
catalog — keep the good trigger wording in the frontmatter, not here.

## Full list

| Skill | Purpose |
|-------|---------|
| `/aiconf` | Single entry point for project-template config (invoked by every `aiconf` verb) — assesses whether the project is configured, installs the detected template if not, otherwise compares each deployed artifact against the template and reconciles drift (pull, push, or semantic merge) |
| `/breakdown-milestone` | Break a milestone (e.g. M0) into incremental sprints of working software |
| `/breakdown-sprint` | Break a sprint (e.g. s1) into ordered, parallelizable tasks following agile user-story principles |
| `/check-claude-projects` | Search past session transcripts under `~/.claude/projects` (current project + sibling checkouts) to recover prior context — e.g. a bug fixed in an earlier session you can't locate |
| `/check-notes` | Find information in the user's personal Obsidian vault at `~/wrksp/notes` — reads its hand-maintained `index.md` map to locate the topic, falls back to searching the vault |
| `/code-review` | Code review workflow. Runs 9 language-agnostic aspects, plus auto-detected language reviews (`review-<lang>`) and a per-project `review-project` skill when present |
| `/commit` | Commit only the changes THIS session made (never another agent's work in a shared checkout) — stages by explicit path, hunk-level when a file is co-edited. With a message arg, one commit; with no arg, splits the session's work into the fewest self-contained commits (a feature plus its tests, docs and connected chores stay together) and auto-writes each feat/fix/chore message |
| `/debug-log` | Add debug logging to trace code execution |
| `/deslop` | Copy-edit text to strip AI/LLM writing tells (overused words, significance-inflation phrases, scene-setting openers, em-dash overuse, rule-of-three, "it's not X, it's Y"); `--report` to flag without rewriting |
| `/doc` | Documentation: assess state and run the right action (default, no args — surveys gaps/staleness/quality and routes), or explicit review/update/generate/session (--review, --update, --generate, --session) |
| `/evaluate-tech` | Structured adoption decision for a library, tool, or hosted service — triages hard vs. soft constraints so current architecture never silently eliminates options, enumerates 5-8 candidates wide, then scores every one in parallel against one rubric with maintenance health as a mandatory gate |
| `/explain` | Generate project explanation docs in `docs/explain/` (--architecture, --flows, --syntax, --system, --infra, --test, --all, --staged, optional topic filter) |
| `/guide` | Walk through a multi-step UI/console task (e.g. cloud permission setup), re-printing a live step tracker at the bottom of every reply so you never scroll up |
| `/hard-fix` | Escalation workflow for stubborn bugs |
| `/ideation` | Generate ideas with structure when stumped — on what to build, the real problem, or a solution. Routes frameworks by stuck-state, diverges then converges to a prioritized shortlist (`--problem`, `--feature`, `--solution`, `--quick`) |
| `/improve-agent-instructions` | Audit and improve the always-loaded instruction files (`AGENTS.md`, `CLAUDE.md`, `GEMINI.md`) — scores gotcha density, derivable/duplicated content, progressive disclosure, and conflicting rules; proposes removals as well as additions |
| `/library-docs` | Generate/refresh a per-repo `library-use` reference — official docs + changelog links, pinned versions, and distilled correct-usage conventions for the repo's fast-moving/niche libraries. Re-run version-checks entries: same-API bumps auto-update, API-changing bumps report + draft a migration and ask before applying |
| `/pdf` | PDF processing: read, merge, split, create, fill forms, OCR |
| `/perf-test` | Set up and run performance tests with improvement cycle |
| `/permission` | Manage personal project or shared global shell/MCP permissions across every harness |
| `/plan` | Lightweight middle-tier planning — a read-only Fable subagent drafts a concrete plan (approach, file manifest, ordered steps, risks, open questions), you approve at one go-ahead gate, then Opus implements in auto mode. Never enters plan mode (dodges the plan-mode permission prompts). `--review` runs multi-agent `review-plan` before the gate |
| `/pre-existing` | Force a rigorous investigation of "pre-existing" test/lint/type/CI failures instead of dismissing them |
| `/read-docs` | Search internal project documentation (proactive) |
| `/research-general` | Research a non-technical topic online (academic, news, primary sources, consumer, fact-checks) using parallel agents |
| `/research-tech` | Research any technical/developer topic online using parallel agents — libraries, errors, best practices, tool/library/model comparisons, product capabilities, ecosystem signal |
| `/resolve-conflicts` | Git merge conflict resolution |
| `/review-architecture` | System architecture review — layering, module boundaries, coupling, pattern fit, quality attributes (--staged, --all, --multi) |
| `/review-cleancode` | Clean code principles review — SOLID, DRY, YAGNI, KISS, code smells (--staged, --all, --multi) |
| `/review-comments` | Review and clean up low-quality code comments (--all, --staged, --changed) |
| `/review-history` | Analyze git history and past issue logs |
| `/review-interfaces` | Interface design review for functions, classes, components (--staged, --all) |
| `/review-library-use` | Reviews code against the repo's `library-use` conventions — stale/renamed APIs, deprecated patterns, missing required setup a general reviewer misses. Auto-invoked by `code-review` when a `library-use` reference exists |
| `/review-logs` | Analyze session transcripts for failure patterns and suggest fixes |
| `/review-perf` | Performance analysis (--staged, --all) |
| `/review-plan` | Multi-agent review of implementation plans |
| `/review-product` | Review a product from the user's perspective — build a persona, map use cases, audit friction/gaps (`--live`, `--multi`); writes to `docs/product/`, checks it against `docs/prd/` |
| `/review-security` | Security audit for vulnerabilities (--staged, --all) |
| `/review-swift` | Swift judgment-level review a linter and the compiler can't do — state modeling, optional/error/Codable modeling, concurrency isolation intent, SwiftUI identity/lifetime/dependencies, ARC ownership, escape hatches hiding a modeling problem. Non-overlapping with SwiftLint / Swift 6 strict concurrency. Auto-invoked by `code-review` on Swift projects |
| `/review-typescript` | TypeScript judgment-level review a linter can't do — type modeling, inference-vs-annotation, casts/`any` hiding a modeling problem. Deliberately non-overlapping with typescript-eslint. Auto-invoked by `code-review` on TS projects |
| `/second-opinion` | Get a second opinion |
| `/skill-creator` | Guide for creating skills |
| `/squash-commits` | Squash unpushed commits into clean higher-level feat/fix/chore commits per the commit policy (`--conservative`, optional base ref) |
| `/summary` | Explain staged git changes in detail and propose conventional-commit messages. `--quick` for a recap of the current task and next steps |
| `/temp` | Make temporary code changes for testing, easily undone with `/temp undo` |
| `/test` | Tests: assess state and run the right action (default, no args — runs the suite, then routes failures to fix, gaps to generate, smells to review), or explicit review/generate (--review, --generate) |
| `/time-reconstruct` | Reconstruct what you worked on from git history for time tracking — real complexity assessment from the diff, not its size |

## Detailed usage

### /code-review

Code review workflow with optional multi-model feedback.

**Arguments:**
- `<target>` - File, directory, or PR to review
- `--multi` - Also get a review from Codex

**Example:** `/code-review src/api/ --multi`

Ends with a selectable fix-scope prompt (Critical only / Critical + Should Fix / everything incl. Nice to Have / don't fix) whenever the review found anything actionable.

---

### /debug-log

Add debug logging statements to trace code execution. Supports any language (JS/TS, Python, Go, etc).

**Arguments:**
- `<topic or area to debug>` - What to instrument with logging

**Example:** `/debug-log authentication flow`

---

### /doc

Documentation review and generation.

**Arguments:**
- `--review` - Check existing docs against standards (default)
- `--generate <target>` - Create docs for specified code
- `--staged` - Scope to git staged files
- `--unpushed` - Scope to files changed across all unpushed commits
- `--all` - Scope to entire codebase

**Examples:**
- `/doc --review --staged`
- `/doc --generate src/utils/parser.ts`

---

### /evaluate-tech

Structured adoption decision for a library, tool, or hosted service. Enforces the two things ad-hoc evaluation skips: maintenance health checked for every candidate upfront (so a recommendation never flips once someone thinks to ask), and hard-vs-soft constraint triage — current architecture becomes an integration-cost line, never a silent filter on the candidate pool.

Enumerates 5-8 candidates wide (including the platform primitive, build-it-yourself, and do-nothing), hard-filters, then evaluates each in a parallel sub-agent against one identical rubric. Picks a criteria profile: Library (bundle size, module format, types, peer deps), Tool (install footprint, platform coverage, CI, upgrade history), or Service (pricing at 10x, export completeness, SLA, vendor durability). Reports a comparison matrix in-conversation; writes no files.

Maintenance health is judged on substance, not cadence: bot-vs-human commit split, whether maintainers still answer issues, whether community fixes land, and whether the current major is quietly in maintenance-only mode behind a v-next branch.

For learning how to use something already chosen, or open-ended research, use `/research-tech`.

**Arguments:**
- `<what you need>` — optionally `| candidate, candidate, ...` to seed the list

**Examples:**
- `/evaluate-tech date formatting for our React web app`
- `/evaluate-tech error tracking service | Sentry, Bugsnag, Rollbar`
- `/evaluate-tech linter to replace ESLint`
- `/evaluate-tech is react-native-keychain still worth adopting`

---

### /explain

Explain unfamiliar code grouped by logical concepts. For language learners, includes syntax explanations.

**Arguments:**
- `--staged` - Explain code in git staged files
- `--unpushed` - Explain code changed across all unpushed commits
- `--all` - Interactive file/directory selection
- `--code` - Include language syntax explanations and alternatives
- Default: explain code related to current conversation context

**Examples:**
- `/explain --staged`
- `/explain --all --code`

---

### /hard-fix

Escalation workflow for stubborn bugs. Combines parallel investigation using research-tech, debug-log, review-history, and second-opinion.

**Arguments:**
- `<description of the persistent problem>`

**Example:** `/hard-fix login fails intermittently on iOS`

---

### /pre-existing

Force a thorough investigation of "pre-existing" test, lint, type, build, or CI failures instead of dismissing them. Replaces the old `block-test-dismissal` Stop hook.

**Arguments:**
- `[optional: name of the failing check, file, or error]`

**Example:** `/pre-existing tsc errors in src/api`

---

### /perf-test

Set up and run performance tests (profiling, load testing, or E2E scenarios). Includes improvement cycle to implement fixes and compare results.

**Arguments:**
- `<target>` - File, function, endpoint, or service to test

**Example:** `/perf-test /api/checkout`

---

### /review-plan

Multi-agent review of implementation plans before execution. Spawns parallel agents for external opinions, alternative solutions, and adversarial critique.

**Arguments:**
- `[path to plan file]` - Optional, uses current plan context if omitted

**Example:** `/review-plan`

---

### /read-docs

Search and read internal project documentation (docs/, README.md, CLAUDE.md).

**Arguments:**
- `<keywords or topic>`

**Example:** `/read-docs authentication patterns`

---

### /research-tech

Research a programming topic online using parallel agents. Searches documentation, GitHub issues, and general solutions.

**Arguments:**
- `<topic or error message>`

**Example:** `/research-tech React 19 use() hook`

---

### /research-general

Research a non-programming topic online using parallel agents. Searches Wikipedia, academic papers (arxiv/SSRN), established news outlets, primary government/organizational sources, and forums.

**Arguments:**
- `<question, topic, or claim to verify>`

**Examples:**
- `/research-general what does the evidence say about screen time and adolescent sleep`
- `/research-general "humans only use 10% of their brain"`
- `/research-general nuclear vs solar economics for grid power`

---

### /resolve-conflicts

Resolve git conflicts from any operation (merge, rebase, cherry-pick, stash, revert). Detects conflict type and provides correct continuation commands.

**Arguments:**
- `[file path]` - Optional, resolves all conflicts if omitted

**Example:** `/resolve-conflicts src/index.ts`

---

### /review-comments

Review code comments for quality. Ensures comments explain "why" not "what".

**Arguments:**
- `--all` - Entire codebase (uses parallel agents)
- `--staged` - Git staged files
- `--unpushed` - Files changed across all unpushed commits
- `--changed` - Git unstaged changes
- Default: `--staged --changed` combined

**Example:** `/review-comments --staged`

---

### /review-history

Analyze how code changed over time using git history and past issue logs. Useful for investigating regressions.

**Arguments:**
- `<file, function, or feature area>`

**Example:** `/review-history src/auth/login.ts`

---

### /review-logs

Analyze Claude Code session transcripts for failure patterns (retry loops, permission denials, command failures) and suggest concrete fixes.

**Arguments:**
- `--days N` - Lookback window (default: 14)
- `--project <name>` - Filter to a specific project
- `--verbose` - Include problematic session IDs for manual review

**Examples:**
- `/review-logs`
- `/review-logs --days 30 --project my-app`

---

### /review-perf

Static performance analysis for algorithmic complexity, memory leaks, N+1 queries, and render issues.

**Arguments:**
- `--staged` - Git staged files (default)
- `--unpushed` - Files changed across all unpushed commits
- `--all` - Entire codebase

**Example:** `/review-perf --staged`

---

### /review-security

Security audit for vulnerabilities, secrets, and unsafe patterns. Checks OWASP Top 10, hardcoded secrets, and dependency vulnerabilities.

**Arguments:**
- `--staged` - Git staged files (default)
- `--unpushed` - Files changed across all unpushed commits
- `--all` - Entire codebase

**Example:** `/review-security --all`

---

### /second-opinion

Get input from two independent advisors on the current problem or question — Codex (GPT) and
OpenCode+GLM when invoked from Claude, Claude and OpenCode+GLM when invoked from Codex / Gemini
CLI / Antigravity / Pi. Both variants are generated from `skills/second-opinion.template.md`; edit
that (or `skills/sync.py`), never the `SKILL.md` files.

**Arguments:**
- `--quick` - Single pass, no iteration
- `--timeout=<seconds>` - Timeout per advisor (default `300`)
- `--words=<n>` - Max words per advisor response (default `500`)

**Example:** `/second-opinion --quick`

---

### /skill-creator

Guide for creating effective skills. Use when creating or updating skills.

**Example:** `/skill-creator`

---

### /permission

Manage shell-command and MCP allow, ask, and deny rules across every configured
agent harness. Supports personal project-local rules and shared global rules.

**Example:** `/permission allow pytest locally`

---

### /aiconf

Single entry point for project-template config, invoked by every `aiconf` shell verb. Assesses
whether a project is configured; if not, detects its type (`flutter`, `react-native`, `web`,
`railway`), confirms, and installs it. If it is, compares each deployed artifact (`.mcp.json`,
bundled skills, CLAUDE.md / AGENTS.md snippets) against the template and reconciles drift —
direction per artifact decided from diff + git history, with a semantic merge when both sides
moved. Multiple types can be installed in one project (`railway` composes with `web`).

**Examples:**
- `/aiconf` (from inside a project dir)
- `/aiconf /path/to/project` (from `~/ac`)
- `/aiconf sync` (skip detection, go straight to sync)
- `/aiconf flutter` (skip detection, install a known type)

---

### /test

Test review and generation.

**Arguments:**
- `--review` - Check test quality (default)
- `--generate <target>` - Create tests for specified code
- `--staged` - Scope to git staged files
- `--unpushed` - Scope to files changed across all unpushed commits
- `--all` - Scope to entire codebase

**Examples:**
- `/test --review --staged`
- `/test --generate src/utils/parser.ts`
