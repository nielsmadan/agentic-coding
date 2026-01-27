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
| `/plan-review` | Multi-agent review of implementation plans |
| `/read-docs` | Search docs/ folder |
| `/research-online` | Research a topic online using parallel agents |
| `/resolve-conflicts` | Git merge conflict resolution |
| `/review-history` | Analyze git history and past issue logs |
| `/review-comments` | Review code comments (--all, --staged, --changed) |
| `/doc` | Documentation review and generation (--review, --generate) |
| `/test` | Test review and generation (--review, --generate) |
| `/rn-upgrade` | React Native upgrade workflow |
| `/second-opinion` | Get a second opinion |
| `/skill-creator` | Guide for creating skills |

## Permissions Policy

The Claude settings enforce a read-only git policy:
- **Allowed**: All read-only git commands, file inspection, web search/fetch
- **Denied**: All git commands that modify state (commit, push, merge, reset, checkout, etc.)

## Keyword Triggers

When the user's prompt contains "second opinion", automatically invoke the `/second-opinion` skill to get external advisor input.

When the user's prompt contains "research online", automatically invoke the `/research-online` skill to search documentation, GitHub issues, and web resources in parallel.

When the user's prompt contains "review plan", "review the plan", or "review my plan", automatically invoke the `/plan-review` skill to get multi-agent feedback before implementation.

When the user's prompt contains "add debug logs" or "debug logging", automatically invoke the `/debug-log` skill to instrument code with tracing.

When the user's prompt contains "review history" or "git history" or "how did this change", automatically invoke the `/review-history` skill to analyze code evolution.
