---
name: permission
description: Manage shell-command and MCP allow, ask, and deny rules across Claude, Codex, Antigravity, OpenCode, and Pi. Use when the user invokes permission, says "allow this command locally/globally", "don't ask for this command", "deny this tool", "change permissions", "list permissions", or asks to regenerate agent permission rules.
argument-hint: allow|ask|deny|remove|list target locally|globally
---

# Permission

## Instructions

### Step 1: Parse the request

Resolve the action (`allow`, `ask`, `deny`, `remove`, `list`, or `sync`), scope
(`local` or `global`), and kind (shell by default; MCP when named). Ask for scope
when omitted. Use `server/*` for an MCP server or `server/tool` for one tool.

### Step 2: Preview safely

Use `--dry-run` when command resolution or target selection is ambiguous:

```sh
aiperm allow --scope local --shell pytest --dry-run
aiperm allow --scope global --mcp jina/read_url --dry-run
```

For a local bare executable, `aiperm` detects an unambiguous virtual-environment
path. Tell the user the exact resolved prefix. Never broaden a rule.

### Step 3: Apply and verify

Run the command without `--dry-run`. It updates the canonical source, regenerates
native harness configurations, and prints affected or pending adapters.

```sh
aiperm list --scope all
aiperm sync --scope local
aiperm sync --scope global
```

Report the canonical rule and whether a fresh agent session is needed. Do not run
git commands unless the user separately asks.

## Examples

### Example 1: Allow project pytest

User says: "permission allow pytest locally"

Actions:

1. Run `aiperm allow --scope local --shell pytest`.
2. Report `.venv/bin/pytest` when that is the detected executable.
3. Report generated adapters and pending Antigravity registration.

Result: pytest is approved only in the current project.

### Example 2: Approve an MCP server globally

User says: "permission allow MCP jina globally"

Actions:

1. Normalize the target to `jina/*`.
2. Run `aiperm allow --scope global --mcp jina/*`.
3. Report that new sessions load the regenerated approval configuration.

Result: Jina tools are approved across configured harnesses.

### Example 3: Remove a rule

User says: "permission remove pytest locally"

Actions:

1. Resolve the same local executable used when the rule was added.
2. Run `aiperm remove --scope local --shell pytest`.

Result: only the managed pytest rule is removed.

## Troubleshooting

### Antigravity is pending

**Cause:** The project has not been opened in Antigravity.

**Solution:** Open it once, then run `aiperm sync --scope local`.

### A personal output is tracked

**Cause:** Local mode will not modify a tracked native config.

**Solution:** Use global scope or explicitly choose a team-shared workflow.

### A shell rule is rejected

**Cause:** Portable rules do not accept globs, pipes, substitutions, or redirects.

**Solution:** Grant the smallest executable-and-argument prefix all harnesses express.
