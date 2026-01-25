#!/bin/bash
# Juggler hook script for Claude Code
# Posts session state changes to Juggler

EVENT="$1"
JUGGLER_PORT="${JUGGLER_PORT:-7483}"

# Read JSON input from stdin (Claude Code passes hook data via stdin)
INPUT=$(cat)

# Extract fields from the JSON input using Python (jq may not be installed)
SESSION_ID=$(echo "$INPUT" | python3 -c "import sys, json; print(json.load(sys.stdin).get('session_id', 'unknown'))" 2>/dev/null || echo "unknown")
TRANSCRIPT_PATH=$(echo "$INPUT" | python3 -c "import sys, json; print(json.load(sys.stdin).get('transcript_path', ''))" 2>/dev/null || echo "")

# Get iTerm session ID from environment (if available)
ITERM_SESSION_ID="${ITERM_SESSION_ID:-}"

# Get git info (if in a git repo)
GIT_BRANCH=$(git -C "$PWD" rev-parse --abbrev-ref HEAD 2>/dev/null || echo "")
GIT_REPO=$(basename "$(git -C "$PWD" rev-parse --show-toplevel 2>/dev/null)" 2>/dev/null || echo "")

# Build JSON payload
JSON=$(cat <<EOF
{
    "session_id": "${SESSION_ID}",
    "iterm_session_id": "${ITERM_SESSION_ID}",
    "cwd": "${PWD}",
    "transcript_path": "${TRANSCRIPT_PATH}",
    "git_branch": "${GIT_BRANCH}",
    "git_repo": "${GIT_REPO}"
}
EOF
)

# Post to Juggler (ignore errors if Juggler isn't running)
curl -s -X POST "http://localhost:${JUGGLER_PORT}/session/${EVENT}" \
    -H "Content-Type: application/json" \
    -d "$JSON" \
    --connect-timeout 1 \
    >/dev/null 2>&1 || true
