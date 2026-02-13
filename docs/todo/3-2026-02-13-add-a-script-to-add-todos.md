# Add a CLI command to create todos via Claude

A shell script (e.g. `todo` or `ct`) that lets you run something like `todo --prio 1 fix login crash` from the terminal. Under the hood it calls `claude -p` with the `/todo` skill to create the todo file, so you get the same smart expansion behavior without opening an interactive session.

The user experience: type a quick command, get a todo file created in `docs/todo/` with the right priority and slug, see a one-line confirmation.

## Context
- Claude CLI supports `claude -p` for non-interactive single-prompt mode
- `/todo` skill: `claude/skills/todo/SKILL.md`
- Existing hook scripts: `claude/hooks/`
