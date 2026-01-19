#!/bin/bash

# Debug: log hook trigger
echo "$(date): on_waiting_for_input triggered, ITERM_SESSION_ID=$ITERM_SESSION_ID" >> /tmp/claude_hook_debug.log

SCRIPT_DIR="$(dirname "$0")"

# Get the full path to python3 (works with pyenv, homebrew, system python)
PYTHON3_PATH="$(command -v python3)"
if command -v pyenv &> /dev/null; then
    PYTHON3_PATH="$(pyenv which python3 2>/dev/null || echo "$PYTHON3_PATH")"
fi

if command -v terminal-notifier &> /dev/null && [ -n "$ITERM_SESSION_ID" ] && [ -n "$PYTHON3_PATH" ]; then
    # Check if session is already active (focused) - skip everything if so
    if "$PYTHON3_PATH" "$SCRIPT_DIR/check_session_active.py" "$ITERM_SESSION_ID" 2>/dev/null; then
        echo "$(date): session active, skipping queue add" >> /tmp/claude_hook_debug.log
        # Session already focused, just ring the bell
        echo -e "\a"
        exit 0
    else
        echo "$(date): session NOT active, adding to queue" >> /tmp/claude_hook_debug.log
    fi

    # Add session to queue (if not already present)
    QUEUE_FILE="$HOME/.claude_session_queue"
    if ! grep -qxF "$ITERM_SESSION_ID" "$QUEUE_FILE" 2>/dev/null; then
        echo "$ITERM_SESSION_ID" >> "$QUEUE_FILE"
    fi

    # Use printf %q to properly escape paths with spaces or special characters
    ESCAPED_SCRIPT="$(printf '%q' "$SCRIPT_DIR/activate_iterm_session.py")"
    ESCAPED_SESSION_ID="$(printf '%q' "$ITERM_SESSION_ID")"

    terminal-notifier \
        -title "Claude Code" \
        -message "Claude is waiting for your input" \
        -sound Glass \
        -execute "$PYTHON3_PATH $ESCAPED_SCRIPT $ESCAPED_SESSION_ID"
elif command -v terminal-notifier &> /dev/null; then
    terminal-notifier \
        -title "Claude Code" \
        -message "Claude is waiting for your input" \
        -sound Glass \
        -activate com.googlecode.iterm2
else
    osascript -e 'display notification "Claude is waiting for your input" with title "Claude Code" sound name "Glass"'
fi

echo -e "\a"
