# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This repository contains shared configuration for agentic coding tools. It includes custom commands, hooks, and permission settings that can be used across multiple projects.

## Structure

- `claude/` - Claude Code specific configuration
  - `settings.json` - Permissions (allowed/denied commands), hooks, and status line config
  - `commands/` - Custom slash commands (skills) in markdown format
  - `hooks/` - Shell scripts triggered by events (e.g., notification when waiting for input)

## Custom Slash Commands

Available in `claude/commands/`:

| Command | Purpose |
|---------|---------|
| `/code-review` | Code review workflow |
| `/debate` | AI debate hub |
| `/flutter-upgrade` | Flutter upgrade workflow |
| `/read-docs` | Search docs/ folder |
| `/resolve-conflicts` | Git merge conflict resolution |
| `/review-comments` | Review code comments |
| `/review-comments-changed` | Review comments on changed files |
| `/review-docs` | Documentation review |
| `/rn-upgrade` | React Native upgrade workflow |
| `/second-opinion` | Get a second opinion |

## Permissions Policy

The Claude settings enforce a read-only git policy:
- **Allowed**: All read-only git commands, file inspection, web search/fetch
- **Denied**: All git commands that modify state (commit, push, merge, reset, checkout, etc.)
