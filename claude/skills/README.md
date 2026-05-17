# Skills

Skills extend Claude Code with specialized workflows and capabilities. Invoke them with `/<skill-name>` followed by any arguments.

## Available Skills

### /code-review

Code review workflow with optional multi-model feedback.

**Arguments:**
- `<target>` - File, directory, or PR to review
- `--multi` - Also get reviews from Gemini and Codex

**Example:** `/code-review src/api/ --multi`

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
- `--all` - Scope to entire codebase

**Examples:**
- `/doc --review --staged`
- `/doc --generate src/utils/parser.ts`

---

### /explain

Explain unfamiliar code grouped by logical concepts. For language learners, includes syntax explanations.

**Arguments:**
- `--staged` - Explain code in git staged files
- `--all` - Interactive file/directory selection
- `--code` - Include language syntax explanations and alternatives
- Default: explain code related to current conversation context

**Examples:**
- `/explain --staged`
- `/explain --all --code`

---

### /hard-fix

Escalation workflow for stubborn bugs. Combines parallel investigation using research-code, debug-log, review-history, and second-opinion.

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

### /research-code

Research a programming topic online using parallel agents. Searches documentation, GitHub issues, and general solutions.

**Arguments:**
- `<topic or error message>`

**Example:** `/research-code React 19 use() hook`

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
- `--all` - Entire codebase

**Example:** `/review-perf --staged`

---

### /review-security

Security audit for vulnerabilities, secrets, and unsafe patterns. Checks OWASP Top 10, hardcoded secrets, and dependency vulnerabilities.

**Arguments:**
- `--staged` - Git staged files (default)
- `--all` - Entire codebase

**Example:** `/review-security --all`

---

### /workbench

Run code in a persistent Docker-sandboxed environment. Iteratively develop scripts with full isolation from the host. Container persists across tasks with Python, Node.js, Go, and Bash pre-installed.

**Arguments:**
- `<task description>` - What to build

**Example:** `/workbench build a python script that reads a CSV and outputs summary stats`

---

### /rn-upgrade

React Native upgrade workflow.

**Arguments:**
- `<target version>` - Version to upgrade to

**Example:** `/rn-upgrade 0.73`

---

### /second-opinion

Get input from Gemini and Codex on the current problem or question.

**Arguments:**
- `--quick` - Single pass, no iteration

**Example:** `/second-opinion --quick`

---

### /skill-creator

Guide for creating effective skills. Use when creating or updating skills.

**Example:** `/skill-creator`

---

### /sync-project-config

Bidirectional sync between a project's deployed Claude config (`.mcp.json`, bundled skills,
CLAUDE.md snippet) and its canonical template in `~/ac/templates/<type>/`. Direction per
artifact is decided from diff + git history. Invoked by `aiconf sync`.

**Examples:**
- `/sync-project-config` (from inside a project dir)
- `/sync-project-config /path/to/project` (from `~/ac`)

---

### /test

Test review and generation.

**Arguments:**
- `--review` - Check test quality (default)
- `--generate <target>` - Create tests for specified code
- `--staged` - Scope to git staged files
- `--all` - Scope to entire codebase

**Examples:**
- `/test --review --staged`
- `/test --generate src/utils/parser.ts`
