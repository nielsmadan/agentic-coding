#!/bin/bash
# Add session to completed queue when task finishes

SCRIPT_DIR="$(dirname "$0")"

# Get the full path to python3 (works with pyenv, homebrew, system python)
PYTHON3_PATH="$(command -v python3)"
if command -v pyenv &> /dev/null; then
    PYTHON3_PATH="$(pyenv which python3 2>/dev/null || echo "$PYTHON3_PATH")"
fi

if [ -n "$ITERM_SESSION_ID" ]; then
    QUEUE_FILE="$HOME/.claude_completed_queue"

    # Remove any existing entry for this session (to re-add at end for recency)
    if [ -f "$QUEUE_FILE" ]; then
        grep -vxF "$ITERM_SESSION_ID" "$QUEUE_FILE" > "$QUEUE_FILE.tmp" && mv "$QUEUE_FILE.tmp" "$QUEUE_FILE"
    fi

    # Add to end of queue (most recent last)
    echo "$ITERM_SESSION_ID" >> "$QUEUE_FILE"

    # Check if session is already active (focused) - skip notification if so
    if [ -n "$PYTHON3_PATH" ] && "$PYTHON3_PATH" "$SCRIPT_DIR/check_session_active.py" "$ITERM_SESSION_ID" 2>/dev/null; then
        # Session already focused, just ring the bell
        echo -e "\a"
        exit 0
    fi

    # Ring bell to indicate completion
    echo -e "\a"
fi
