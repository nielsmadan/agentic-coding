#!/bin/bash
# Hook: PermissionRequest — auto-approve jina MCP tools in every mode, incl. plan.
#
# Why this exists: Claude Code v2.1.198/199 (2026-07-01/02) reworked plan mode's
# permission gate to per-call read-only *classification* instead of consulting
# permissions.allow. Third-party MCP tools (mcp__jina__*) can't be verified as
# read-only, so plan mode now prompts for them despite the `mcp__jina` allow rule
# (which still works silently in auto mode). Upstream bug, no fix released:
#   https://github.com/anthropics/claude-code/issues/76238
#
# Why PermissionRequest, not PreToolUse: per the docs, a PreToolUse hook's
# `allow` does NOT bypass permission rules — an ask/prompt still fires. The
# PermissionRequest hook runs AT the prompt and can auto-answer it. Scoped to
# jina only — read-only web search/fetch with no side effects, so pre-approving
# during planning is safe.

input=$(cat)
tool=$(echo "$input" | jq -r '.tool_name // ""' 2>/dev/null)

case "$tool" in
  mcp__jina__*)
    jq -n '{
      hookSpecificOutput: {
        hookEventName: "PermissionRequest",
        decision: { behavior: "allow" }
      }
    }'
    exit 0
    ;;
esac

# Not a jina tool — stay silent, let the normal prompt proceed.
exit 0
