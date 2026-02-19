# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This repository contains shared configuration for agentic coding tools. It includes skills, hooks, and permission settings that can be used across multiple projects.

## Structure

- `claude/` - Claude Code specific configuration
  - `settings.json` - Permissions (allowed/denied commands), hooks, and status line config
  - `skills/` - Custom skills in `<skill-name>/SKILL.md` format
  - `hooks/` - Shell scripts triggered by events (e.g., notification when waiting for input)

## Skills

Available in `claude/skills/`:

| Skill | Purpose |
|-------|---------|
| `/code-review` | Code review workflow |
| `/frontend-design` | Build distinctive frontend interfaces with high design quality |
| `/debug-log` | Add debug logging to trace code execution |
| `/flutter-upgrade` | Flutter upgrade workflow |
| `/hard-fix` | Escalation workflow for stubborn bugs |
| `/perf-test` | Set up and run performance tests with improvement cycle |
| `/review-plan` | Multi-agent review of implementation plans |
| `/read-docs` | Search internal project documentation (proactive) |
| `/research-online` | Research a topic online using parallel agents |
| `/resolve-conflicts` | Git merge conflict resolution |
| `/review-history` | Analyze git history and past issue logs |
| `/review-comments` | Review and clean up low-quality code comments (--all, --staged, --changed) |
| `/review-perf` | Performance analysis (--staged, --all) |
| `/review-security` | Security audit for vulnerabilities (--staged, --all) |
| `/doc` | Documentation review and generation (--review, --generate) |
| `/explain` | Explain unfamiliar code grouped by concept (--staged, --all, --code) |
| `/test` | Test review and generation (--review, --generate) |
| `/theme-factory` | Apply professional visual themes to artifacts (presentations, docs, HTML) |
| `/todo` | Capture a todo in Todoist (--prio 1-4) |
| `/workbench` | Run code in a Docker-sandboxed environment |
| `/rn-upgrade` | React Native upgrade workflow |
| `/pdf` | PDF processing: read, merge, split, create, fill forms, OCR |
| `/second-opinion` | Get a second opinion |
| `/review-logs` | Analyze session transcripts for failure patterns and suggest fixes |
| `/skill-creator` | Guide for creating skills |

## Git Policy

**Read-only.** Do not run git commands that modify state (add, commit, push, etc.) - they will fail. Ask the user to run these manually.

## GitHub Commands

Prefer dedicated `gh` subcommands over `gh api`:
- Issue comments: `gh issue view <num> --comments -R <owner/repo>`
- PR comments: `gh pr view <num> --comments -R <owner/repo>`
- PR reviews: `gh pr view <num> --json reviews -R <owner/repo>`
- Releases: `gh release list -R <owner/repo>`
- Workflow runs: `gh run list -R <owner/repo>`

Do NOT use `gh api` when a dedicated subcommand exists.

## Verification Policy

Never claim "best practice", "recommended", "accepted solution", or "community consensus" without a cited source. If you haven't verified something, say "I believe" or "this might work" - not "this is the way."

**Do NOT say:**
- "This is the accepted approach" → without a source, you don't know this
- "The community recommends" → find a citation or don't claim consensus
- "This is best practice" → according to whom?

When unsure, be explicit: "I think this will work, but I haven't verified it's the recommended approach."

## Test & Lint Failures

Never dismiss test failures, linting errors, or type errors as "pre-existing issues." Fix them. All repos use pre-commit hooks that enforce clean tests and linting — if something fails after your changes, either your changes caused it or it needs fixing regardless. Do not:
- Skip failing tests by claiming they were already broken
- Suggest the user "ignore" lint errors
- Offer to "move on" without fixing failures

If a failure is genuinely unrelated to your changes, fix it anyway and note that it was pre-existing.

## Keyword Triggers

When the user's prompt contains "second opinion", automatically invoke the `/second-opinion` skill to get external advisor input.

When the user's prompt contains "research online", automatically invoke the `/research-online` skill to search documentation, GitHub issues, and web resources in parallel.

When the user's prompt contains "review plan", "review the plan", or "review my plan", automatically invoke the `/review-plan` skill to get multi-agent feedback before implementation.

When the user's prompt contains "add debug logs" or "debug logging", automatically invoke the `/debug-log` skill to instrument code with tracing.

When the user's prompt contains "review history" or "git history" or "how did this change", automatically invoke the `/review-history` skill to analyze code evolution.

When the user's prompt contains "workbench", automatically invoke the `/workbench` skill to run code in a Docker-isolated environment.

When the user's prompt mentions `.pdf` files or asks to work with PDFs (merge, split, extract text, create, fill forms, OCR, watermark), automatically invoke the `/pdf` skill.

When the user's prompt asks to build or design a web page, landing page, dashboard, or component, or to beautify/style a web UI, automatically invoke the `/frontend-design` skill.

When the user's prompt contains "review logs", "session analysis", or "failure patterns", automatically invoke the `/review-logs` skill to analyze session transcripts.

## Proactive Workbench Usage

Proactively suggest or use `/workbench` when:
- The user asks to write a script that processes files (CSV parsers, data transforms, etc.) and you'd otherwise run it directly on the host
- The user asks to prototype or experiment with untrusted code, unfamiliar libraries, or generated code
- The task involves running code that does filesystem operations (delete, move, overwrite) where a mistake could damage the project
- The user asks to "try something out", "prototype", or "experiment" with code
- You're about to run `python`, `node`, or `bash` on a user-written script that wasn't part of the existing project

Do NOT use workbench for: running existing project test suites, build commands, linters, or other project tooling that's already configured.

## Internal Documentation

When a `docs/` folder exists, proactively check internal documentation using `/read-docs`:

**Automatic triggers:**
- Before planning a new feature or significant change
- When entering a new area of the codebase for the first time
- When debugging issues (check for documented gotchas)
- When the user asks about conventions, patterns, or architecture

This supplements CLAUDE.md with detailed project-specific knowledge. For external library docs, use `/research-online` instead.
