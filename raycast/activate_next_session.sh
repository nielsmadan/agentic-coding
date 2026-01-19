#!/bin/bash

# Required for Raycast Script Commands
# @raycast.schemaVersion 1
# @raycast.title Next Claude Session
# @raycast.mode silent
# @raycast.icon 🤖

QUEUE_FILE="$HOME/.claude_session_queue"
SCRIPT_DIR="$HOME/.claude/hooks"

# Get python3 path
PYTHON3_PATH="$(command -v python3)"
if command -v pyenv &> /dev/null; then
    PYTHON3_PATH="$(pyenv which python3 2>/dev/null || echo "$PYTHON3_PATH")"
fi

if [ ! -f "$QUEUE_FILE" ] || [ ! -s "$QUEUE_FILE" ]; then
    echo "No sessions waiting"
    exit 0
fi

# Get first session from queue
SESSION_UUID=$(head -n 1 "$QUEUE_FILE")

if [ -n "$SESSION_UUID" ] && [ -n "$PYTHON3_PATH" ]; then
    # Remove from queue
    tail -n +2 "$QUEUE_FILE" > "$QUEUE_FILE.tmp" && mv "$QUEUE_FILE.tmp" "$QUEUE_FILE"

    # Activate the session
    "$PYTHON3_PATH" "$SCRIPT_DIR/activate_iterm_session.py" "$SESSION_UUID"

    # Count remaining
    remaining=$(wc -l < "$QUEUE_FILE" 2>/dev/null | tr -d ' ')
    if [ "$remaining" -gt 0 ]; then
        echo "$remaining more waiting"
    else
        echo "Queue empty"
    fi
else
    echo "No valid session"
fi
