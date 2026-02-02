#!/bin/bash
# Juggler hook script for Claude Code
# Posts hook events to Juggler using unified payload format

EVENT="$1"
JUGGLER_PORT="${JUGGLER_PORT:-7483}"

# Read raw JSON input from stdin (Claude Code passes hook data via stdin)
HOOK_INPUT=$(cat)

# Get iTerm session ID from environment (if available)
ITERM_SESSION_ID="${ITERM_SESSION_ID:-}"

# Get git info (if in a git repo)
GIT_BRANCH=$(git -C "$PWD" rev-parse --abbrev-ref HEAD 2>/dev/null || echo "")
GIT_REPO=$(basename "$(git -C "$PWD" rev-parse --show-toplevel 2>/dev/null)" 2>/dev/null || echo "")

# Build unified payload using Python (handles JSON escaping properly)
JSON=$(python3 << PYTHON
import json
import sys

# Parse hook input (may be empty for some events)
hook_input = {}
raw_input = '''$HOOK_INPUT'''
if raw_input.strip():
    try:
        hook_input = json.loads(raw_input)
    except json.JSONDecodeError:
        pass

payload = {
    "agent": "claude-code",
    "event": "$EVENT",
    "hookInput": hook_input,
    "terminal": {
        "sessionId": "$ITERM_SESSION_ID",
        "cwd": "$PWD"
    },
    "git": {
        "branch": "$GIT_BRANCH",
        "repo": "$GIT_REPO"
    }
}

print(json.dumps(payload))
PYTHON
)

# Post to Juggler (ignore errors if Juggler isn't running)
curl -s -X POST "http://localhost:${JUGGLER_PORT}/hook" \
    -H "Content-Type: application/json" \
    -d "$JSON" \
    --connect-timeout 1 \
    >/dev/null 2>&1 || true
