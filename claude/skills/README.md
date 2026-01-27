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

### /flutter-upgrade

Workflow for upgrading Flutter and dependencies following best practices.

**Example:** `/flutter-upgrade`

---

### /hard-fix

Escalation workflow for stubborn bugs. Combines parallel investigation using research-online, debug-log, review-history, and second-opinion.

**Arguments:**
- `<description of the persistent problem>`

**Example:** `/hard-fix login fails intermittently on iOS`

---

### /perf-test

Set up and run performance tests (profiling, load testing, or E2E scenarios). Includes improvement cycle to implement fixes and compare results.

**Arguments:**
- `<target>` - File, function, endpoint, or service to test

**Example:** `/perf-test /api/checkout`

---

### /plan-review

Multi-agent review of implementation plans before execution. Spawns parallel agents for external opinions, alternative solutions, and adversarial critique.

**Arguments:**
- `[path to plan file]` - Optional, uses current plan context if omitted

**Example:** `/plan-review`

---

### /read-docs

Search and read internal project documentation (docs/, README.md, CLAUDE.md).

**Arguments:**
- `<keywords or topic>`

**Example:** `/read-docs authentication patterns`

---

### /research-online

Research a programming topic online using parallel agents. Searches documentation, GitHub issues, and general solutions.

**Arguments:**
- `<topic or error message>`

**Example:** `/research-online React 19 use() hook`

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
