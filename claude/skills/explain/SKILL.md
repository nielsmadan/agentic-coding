---
name: explain
description: "Generate project explanation docs in docs/explain/ covering architecture, language syntax, system APIs, infrastructure, or testing. Use when the user wants to understand an unfamiliar project or codebase. Supports --all (every aspect), --staged (scope to git-staged files), --architecture, --syntax, --system, --infra, --test, optionally followed by a topic filter (e.g. `--architecture database`)."
argument-hint: "[--all | --architecture | --syntax | --system | --infra | --test] [--staged] [topic]"
---

# Explain

Generate project explanation documents in `docs/explain/`. Each aspect of the project gets its own file. An `overview.md` acts as the index (opened first); a `preliminary.md` carries the shared project context every other doc assumes.

## Flags

| Flag | What it covers |
|------|----------------|
| `--architecture` | Components, data flow, layering. Pros/cons of the current design **and** at least one alternative structuring with its tradeoffs. |
| `--syntax` | Non-obvious language features actually used in the project. Skip basics like `for` loops. Where the language offers multiple ways to do the same thing, list them with pros/cons. |
| `--system` | System-level APIs in use (filesystem, networking, process, IPC, OS-specific). For each, list alternatives with pros/cons. |
| `--infra` | Build, CI/CD, deploy, release pipelines. Include how to run each piece locally (scripts, commands, env setup). |
| `--test` | Testing infrastructure: frameworks, test types, fixtures, how to run. |
| `--all` | All five aspects above, dispatched to parallel sub-agents. |
| `--staged` | Scope to files returned by `git diff --cached --name-only`. Combines with any aspect flag(s). |
| _topic_ | A positional word after an aspect flag narrows the focus (e.g. `--architecture database` = architecture of the database layer only). |

## Usage

```
/explain --all                      # Full project explanation
/explain --architecture             # Just architecture
/explain --architecture database    # Architecture, focused on the database
/explain --staged --architecture    # Architecture needed to understand staged changes
/explain --staged --all             # All aspects, scoped to staged files
/explain --infra                    # CI/CD + local setup
```

## Workflow

### 1. Parse arguments
- Collect requested aspect flags. `--all` expands to all five.
- Check for `--staged`.
- Capture any positional topic filter that follows an aspect flag, and pass it to that aspect's sub-agent only.
- If no aspect flag and no `--all` was given, ask the user which aspect(s) to cover before proceeding.

### 2. Determine scope

| Mode | Scope |
|------|-------|
| `--staged` set | Output of `git diff --cached --name-only` |
| `--staged` not set | Whole project (respect `.gitignore`, skip `node_modules/`, `build/`, `dist/`, lockfiles, binaries) |

Empty scope: if `--staged` is set but nothing is staged, tell the user to stage files first or drop `--staged`. Do not proceed.

### 3. Write `preliminary.md` first
Before dispatching aspect sub-agents, write `docs/explain/preliminary.md`. Keep it tight — just enough shared context that a new reader can follow the other docs:
- Project name and purpose
- Primary language(s) and major frameworks
- Top-level directory layout
- Entry points (main binary, app root, server entry)

Every aspect sub-agent should be told to assume readers have read `preliminary.md` and link to it rather than restate its content.

### 4. Run aspect sub-agents in parallel
For each requested aspect, dispatch an `Agent` sub-agent in a single message so they execute concurrently. Prefer `subagent_type: "Explore"` for research-heavy aspects (`--architecture`, `--syntax`, `--system`), `general-purpose` for `--infra` and `--test` since they may need to run commands.

Each sub-agent prompt must include:
- The aspect name (e.g. "architecture")
- The exact scope (list of staged files, or "whole project" with `.gitignore` honored)
- The topic filter, if any
- The target output path (`docs/explain/<aspect>.md`)
- The per-aspect rubric (see below) copied into the prompt
- The file format template (see Output)
- Instructions to link to siblings using the "See also" block

### 5. Write `overview.md`
After sub-agents return, write `docs/explain/overview.md` as the entry index: short intro, link to `preliminary.md`, one link per generated aspect file with a one-line summary. In the final chat response, tell the user to open `overview.md` first.

## Output

All output goes to `docs/explain/`. Existing files there are overwritten — this is generated content, not hand-written.

```
docs/explain/
├── overview.md        # Index; open this first
├── preliminary.md     # Project context needed to read the rest
├── architecture.md    # If --architecture or --all
├── syntax.md          # If --syntax or --all
├── system.md          # If --system or --all
├── infra.md           # If --infra or --all
└── test.md            # If --test or --all
```

### File format (per-aspect)

```markdown
# [Aspect Title]

**Scope:** [whole project | staged files: path/a, path/b, …]
**Topic filter:** [none | database | …]
**See also:** [overview](overview.md) · [preliminary](preliminary.md) · [architecture](architecture.md) · [syntax](syntax.md) · [system](system.md) · [infra](infra.md) · [test](test.md)

[Body following the per-aspect rubric]
```

Only link to siblings that were actually generated in this run.

### Per-aspect rubrics

**architecture.md**
- Component/module map with data flow and boundaries
- Major design decisions, each with pros/cons
- For each major decision: at least one alternative structuring, with its pros/cons
- Reference real files/functions, not vague labels

**syntax.md**
- Notable language features the project uses (macros, operators, type-system quirks, idioms)
- For each: what it does, why it's used here, alternatives the language offers, pros/cons
- Omit anything a general programmer already knows

**system.md**
- System APIs in use (OS, filesystem, network, process, IPC, hardware)
- For each: what it does in this project, why this one, alternatives with pros/cons

**infra.md**
- Build system, CI/CD pipelines, release flow, deployment targets
- For each pipeline/script: what it does, where it lives, exact command(s) to run it locally, prerequisites, env vars

**test.md**
- Test frameworks in use; unit/integration/e2e split
- Directory layout, fixtures, mocks
- Exact commands to run the full suite and a single test

### overview.md format

```markdown
# Explanation Overview

Start here. Read [preliminary](preliminary.md) next for the shared context the
other docs assume.

**Scope:** [whole project | staged files: …]

## Aspects
- [Architecture](architecture.md) — one-line summary
- [Syntax](syntax.md) — one-line summary
- [System APIs](system.md) — one-line summary
- [Infrastructure](infra.md) — one-line summary
- [Testing](test.md) — one-line summary
```

Only include bullets for aspects actually generated this run.

## Examples

### `/explain --all`
Writes `preliminary.md`, dispatches five parallel sub-agents (one per aspect), writes `overview.md` last. Final chat message lists the files and tells the user to open `overview.md` first.

### `/explain --staged --architecture`
`git diff --cached --name-only` → staged files. Write a focused `preliminary.md` covering the surrounding modules. Dispatch one sub-agent to produce `architecture.md` limited to what is needed to understand the staged change. Write `overview.md` linking only to `preliminary.md` and `architecture.md`.

### `/explain --architecture database`
Whole-project scope. Write `preliminary.md`. Dispatch one architecture sub-agent with topic filter `database`. `architecture.md` covers the database layer's structure, decisions, and alternatives only. `overview.md` links to the two generated files.

## Troubleshooting

### No staged files
"No staged files found. Stage files with `git add` first, or drop `--staged` to cover the whole project." Do not fall back to the whole project silently.

### Aspect not applicable to the project
E.g. `--infra` on a project with no CI/CD. Generate the file anyway with a clear "No CI/CD configured. Build runs manually via `…`" note, and still link to it from `overview.md`. Silent omission leaves the user wondering.

### Project too large for one sub-agent
The sub-agent can split by top-level directory and run its own parallel reads. If output is still incomplete, re-run the specific aspect flag (with a topic filter if helpful) rather than `--all`.

### Docs went stale after code changes
`docs/explain/` is regenerated, not incrementally updated. Re-run the relevant flags; existing files are overwritten.

## Notes
- Group by aspect, not by file. Within an aspect, cite real files/functions.
- Do not restate `preliminary.md` content inside aspect docs — link to it.
- Only link to sibling files that exist in this run; don't produce broken links.
