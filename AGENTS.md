# AGENTS.md

Guidelines for agentic coding tools operating in this repository.

## Repository Overview

Shared configuration for agentic coding tools (Claude Code, Codex, Antigravity, OpenCode). Contains skills, hooks, permissions, and documentation for customizing AI coding assistants.

## Project Structure

```
/
├── claude/           # Claude Code + Claude Desktop configuration
│   ├── settings.json # Hooks, status line; permissions.* arrays are GENERATED
│   ├── CLAUDE.md, CLAUDE.autonomous.md  # global Claude guidance — GENERATED (see Global Instructions)
│   ├── skills/       # Claude Code skills (<name>/SKILL.md)
│   ├── desktop/      # Claude Desktop skills (zip-and-upload)
│   └── hooks/        # Shell scripts for event triggers
├── codex/            # OpenAI Codex CLI configuration
│   ├── rules/        # Permission rules (permissions.rules is GENERATED)
│   └── skills/       # Codex-specific overrides; install.sh syncs the curated subset of claude/skills/ to ~/.agents/skills/
├── antigravity/      # Antigravity CLI (`agy`) configuration
│   └── settings.json # permissions.* arrays are GENERATED (rest of file editable)
├── opencode/         # OpenCode configuration
│   └── opencode.json # permission.bash is GENERATED
├── permissions/      # Single source of truth for agent permissions
│   ├── permissions.toml  # the source — edit this
│   └── sync.py           # regenerates every agent's permission config
├── global/           # Single source of truth for agents' GLOBAL instructions
│   ├── fragments/    # shared prose sections — edit these
│   ├── sync.py       # assembles fragments into each agent's global instruction file
│   └── AGENTS.md     # GENERATED shared file for every non-Claude agent → ~/.codex/AGENTS.md + ~/.gemini/GEMINI.md
├── docs/             # Documentation
└── CLAUDE.md         # Main project instructions
```

## Permissions

Shell-command permissions for all four agents are generated from
**`permissions/permissions.toml`** by `permissions/sync.py`. Never hand-edit the
generated permission files (`claude/settings.json` permission arrays,
`codex/rules/permissions.rules`, `antigravity/settings.json`, `opencode/opencode.json`
`permission.bash`) — a lefthook pre-commit hook (`sync.py --check`) rejects drift.
To change permissions: edit the TOML, run `python3 permissions/sync.py`.

## Global Instructions

Each agent's global (machine-wide) natural-language guidance is generated from the
fragments in **`global/fragments/`** by `global/sync.py` — the same generate-and-check
pattern as permissions. Never hand-edit the generated files (`claude/CLAUDE.md`,
`claude/CLAUDE.autonomous.md`, `global/AGENTS.md`); a lefthook hook
(`global/sync.py --check`) rejects drift. To change global guidance: edit a fragment,
run `python3 global/sync.py`. Only Claude gets its own file (it needs the Jina section
and the autonomous variant); every other agent shares `global/AGENTS.md`, symlinked to
`~/.codex/AGENTS.md` and `~/.gemini/GEMINI.md`. A generator (not native `@imports`) is
used because Codex and OpenCode have no in-file import mechanism. OpenCode has no file
of its own — it inherits `~/.claude/CLAUDE.md`.

## Build/Lint/Test Commands

This is a configuration-only repository. No build, lint, or test commands exist.

**Validation approach:**
- Skill syntax: Verify SKILL.md frontmatter is valid YAML
- Hook scripts: Run `bash -n <script.sh>` for syntax check
- Python scripts: Run `python3 -m py_compile <script.py>` for syntax check

## Git Policy

Leave git to the user. Do not run git commands that modify state (`add`, `commit`, `checkout`, `branch`, `merge`, `rebase`, `stash`, etc.) unless the user explicitly asks for that specific operation. A few commands are hard-blocked at the harness level — `git push`, `git branch -d/-D`, `git reset --hard`, `git clean -f*` — because they push to a remote or destroy local work; ask the user to run those manually.

Read-only inspection (`status`, `log`, `diff`, `show`, `branch` listing, etc.) is always fine.

## Secrets

API keys are deliberately kept out of the agent's reach: SOPS-encrypted at rest, injected by zsh wrappers only into the AI CLI subprocesses that need them, never present in the parent shell env. The agent should NOT try to enumerate, decrypt, or echo the secrets store.

- Don't grep shell env / `.airc` / `.zshrc` for API keys — they aren't there.
- Don't run `sops -d`, list variable names, or read `~/.config/sops/age/keys.txt`.
- For HTTP MCPs and wrapped CLI tools, the relevant env var is already present in this process — just call the tool.
- If a needed credential isn't reaching a subprocess, ask the user. Don't try to source it yourself.

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
- "research online" → `/research-code` (programming/library/code) or `/research-general` (academic/historical/consumer/fact-check). Pick by topic; default to `/research-general` if ambiguous.
- "review plan" → `/review-plan`
- "add debug logs" / "debug logging" → `/debug-log`
- "review history" / "git history" → `/review-history`
- ".pdf" or PDF-related tasks → `/pdf`
- Build/design web page/component → `/frontend-design`
- "review logs" / "session analysis" → `/review-logs`

## Claude Desktop Skills

Skills under `claude/desktop/skills/` deploy to Claude Desktop manually (no automation):
1. Edit `claude/desktop/skills/<name>/SKILL.md` (and any `references/`)
2. Run `./claude/desktop/package-skills.sh` to produce `claude/desktop/zips/<name>.zip`
3. Upload the zip via Claude Desktop's UI

Unpacked copies under `~/Library/Application Support/Claude/local-agent-mode-sessions/skills-plugin/...` are read-only — never edit there.

## Available Skills

Invoke with `/<skill-name>`:

| Skill | Purpose |
|-------|---------|
| `/code-review` | Code review with optional multi-model feedback |
| `/debug-log` | Add debug logging to trace execution |
| `/hard-fix` | Escalation workflow for stubborn bugs |
| `/read-docs` | Search internal project documentation |
| `/research-code` | Research a programming topic online with parallel agents |
| `/research-general` | Research a non-programming topic online with parallel agents |
| `/review-plan` | Multi-agent review of implementation plans |
| `/review-security` | Security audit for vulnerabilities |
| `/review-perf` | Performance analysis |
| `/skill-creator` | Guide for creating effective skills |
