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
| `/test` | Test review and generation (--review, --generate) |
| `/workbench` | Run code in a Docker-sandboxed environment |
| `/rn-upgrade` | React Native upgrade workflow |
| `/second-opinion` | Get a second opinion |
| `/skill-creator` | Guide for creating skills |

## Git Policy

**Read-only.** Do not run git commands that modify state (add, commit, push, etc.) - they will fail. Ask the user to run these manually.

## Verification Policy

Never claim "best practice", "recommended", "accepted solution", or "community consensus" without a cited source. If you haven't verified something, say "I believe" or "this might work" - not "this is the way."

**Do NOT say:**
- "This is the accepted approach" → without a source, you don't know this
- "The community recommends" → find a citation or don't claim consensus
- "This is best practice" → according to whom?

When unsure, be explicit: "I think this will work, but I haven't verified it's the recommended approach."

## Keyword Triggers

When the user's prompt contains "second opinion", automatically invoke the `/second-opinion` skill to get external advisor input.

When the user's prompt contains "research online", automatically invoke the `/research-online` skill to search documentation, GitHub issues, and web resources in parallel.

When the user's prompt contains "review plan", "review the plan", or "review my plan", automatically invoke the `/review-plan` skill to get multi-agent feedback before implementation.

When the user's prompt contains "add debug logs" or "debug logging", automatically invoke the `/debug-log` skill to instrument code with tracing.

When the user's prompt contains "review history" or "git history" or "how did this change", automatically invoke the `/review-history` skill to analyze code evolution.

When the user's prompt contains "workbench", automatically invoke the `/workbench` skill to run code in a Docker-isolated environment.

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
