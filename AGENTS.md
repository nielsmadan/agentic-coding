# AGENTS.md

Guidelines for agentic coding tools operating in this repository.

## Repository Overview

Shared configuration for agentic coding tools (Claude Code, Codex, Gemini, OpenCode). Contains skills, hooks, permissions, and documentation for customizing AI coding assistants.

## Project Structure

```
/
├── claude/           # Claude Code configuration
│   ├── settings.json # Permissions, hooks, status line
│   ├── skills/       # Custom skills (<name>/SKILL.md)
│   └── hooks/        # Shell scripts for event triggers
├── codex/            # OpenAI Codex CLI configuration
│   ├── config.toml   # Approval policy, sandbox mode
│   └── rules/        # Permission rules
├── gemini/           # Gemini CLI configuration
│   └── settings.json
├── opencode/         # OpenCode configuration
│   └── opencode.json
├── docs/             # Documentation
│   └── skill-best-practices.md
└── CLAUDE.md         # Main project instructions
```

## Build/Lint/Test Commands

This is a configuration-only repository. No build, lint, or test commands exist.

**Validation approach:**
- Skill syntax: Verify SKILL.md frontmatter is valid YAML
- Hook scripts: Run `bash -n <script.sh>` for syntax check
- Python scripts: Run `python3 -m py_compile <script.py>` for syntax check

## Git Policy

**Read-only.** Do not run git commands that modify state:
- DENIED: `git add`, `git commit`, `git push`, `git pull`, `git merge`, `git rebase`, `git reset`, `git checkout`, `git switch`, `git restore`, `git cherry-pick`, `git revert`, `git stash`, `git branch -d/-D/-m/-M`, `git tag -d/-a`, `git remote add/remove/rename`, `git clean`, `git rm`, `git mv`, `git init`, `git clone`

Ask the user to run these manually.

## Code Style

### Skills (SKILL.md)

**Folder naming:** kebab-case only (e.g., `code-review`, `debug-log`). No spaces, underscores, or capitals.

**Frontmatter (YAML):**
```yaml
---
name: skill-name-in-kebab-case
description: What it does AND when to use it. Include trigger phrases.
---
```

**Required fields:**
- `name`: kebab-case, matches folder name exactly
- `description`: Under 1024 chars, includes WHAT + WHEN + trigger phrases

**Forbidden:** XML tags (`<` `>`), "claude"/"anthropic" in name, README.md inside skill folder.

**Body structure:**
```markdown
# Skill Name

## Instructions
### Step 1: [Action]
Clear, specific commands with expected outputs.

## Examples
### Example 1: [scenario]
User says: "..."
Actions: 1. ... 2. ...
Result: ...

## Troubleshooting
### Error: [Common error]
**Cause:** ...
**Solution:** ...
```

**Size limit:** Keep SKILL.md under ~5,000 words. Move detailed docs to `references/`.

### Shell Scripts (hooks/)

- Use `#!/bin/bash` shebang
- Read input via `$(cat)` and parse with `jq`
- Exit 0 to allow, exit 2 to block with error message
- Keep timeout under 5 seconds
- Comment header: `# Hook: <Event> on <Tool>`

### Python Scripts (scripts/)

- Use `#!/usr/bin/env python3` shebang
- Docstring with usage examples
- Type hints on function signatures
- Imports: stdlib first, then third-party, grouped with blank lines
- Constants in UPPER_SNAKE at module level
- Use `dataclass` for structured data
- Handle errors gracefully with informative messages to stderr

### JSON Configuration

- 2-space indentation
- Alphabetize keys in permission arrays
- Group related permissions with comments

### TOML Configuration

- Use inline comments for context
- Group related settings

## Naming Conventions

| Type | Convention | Example |
|------|------------|---------|
| Skill folders | kebab-case | `code-review` |
| SKILL.md | Exact case | `SKILL.md` |
| Python scripts | snake_case | `extract_signals.py` |
| Shell scripts | kebab-case | `enforce-fix-failures.sh` |
| JSON keys | snake_case | `approval_policy` |

## Error Handling

**Test/Lint Failures:** Never dismiss as "pre-existing issues." Fix ALL failures before proceeding.

**Claiming Best Practices:** Never claim "best practice," "recommended," or "community consensus" without a cited source. Say "I believe" or "this might work" when unsure.

## GitHub Commands

Prefer dedicated `gh` subcommands over `gh api`:
- Issue comments: `gh issue view <num> --comments -R <owner/repo>`
- PR comments: `gh pr view <num> --comments -R <owner/repo>`
- PR reviews: `gh pr view <num> --json reviews -R <owner/repo>`
- Releases: `gh release list -R <owner/repo>`
- Workflow runs: `gh run list -R <owner/repo>`

Do NOT use `gh api` when a dedicated subcommand exists.

## Keyword Triggers

These phrases automatically invoke skills:
- "second opinion" → `/second-opinion`
- "research online" → `/research-online`
- "review plan" → `/review-plan`
- "add debug logs" / "debug logging" → `/debug-log`
- "review history" / "git history" → `/review-history`
- "workbench" → `/workbench`
- ".pdf" or PDF-related tasks → `/pdf`
- Build/design web page/component → `/frontend-design`
- "review logs" / "session analysis" → `/review-logs`

## Available Skills

Invoke with `/<skill-name>`:

| Skill | Purpose |
|-------|---------|
| `/code-review` | Code review with optional multi-model feedback |
| `/debug-log` | Add debug logging to trace execution |
| `/hard-fix` | Escalation workflow for stubborn bugs |
| `/read-docs` | Search internal project documentation |
| `/research-online` | Research topic online with parallel agents |
| `/review-plan` | Multi-agent review of implementation plans |
| `/review-security` | Security audit for vulnerabilities |
| `/review-perf` | Performance analysis |
| `/skill-creator` | Guide for creating effective skills |
| `/workbench` | Run code in Docker-sandboxed environment |
