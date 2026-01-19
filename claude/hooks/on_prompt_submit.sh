#!/bin/bash
# Remove session from queue when user submits input

if [ -n "$ITERM_SESSION_ID" ]; then
    SESSION_UUID="${ITERM_SESSION_ID#*:}"
    QUEUE_FILE="$HOME/.claude_session_queue"

    if [ -f "$QUEUE_FILE" ]; then
        # Remove this session from queue
        grep -vxF "$SESSION_UUID" "$QUEUE_FILE" > "$QUEUE_FILE.tmp" && mv "$QUEUE_FILE.tmp" "$QUEUE_FILE"
    fi
fi
