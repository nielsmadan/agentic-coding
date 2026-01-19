#!/bin/bash

SCRIPT_DIR="$(dirname "$0")"

# Get the full path to python3 (works with pyenv, homebrew, system python)
PYTHON3_PATH="$(command -v python3)"
if command -v pyenv &> /dev/null; then
    PYTHON3_PATH="$(pyenv which python3 2>/dev/null || echo "$PYTHON3_PATH")"
fi

if command -v terminal-notifier &> /dev/null && [ -n "$ITERM_SESSION_ID" ] && [ -n "$PYTHON3_PATH" ]; then
    # Extract the UUID part (after the colon)
    SESSION_UUID="${ITERM_SESSION_ID#*:}"

    # Add session to queue (if not already present)
    QUEUE_FILE="$HOME/.claude_session_queue"
    if ! grep -qxF "$SESSION_UUID" "$QUEUE_FILE" 2>/dev/null; then
        echo "$SESSION_UUID" >> "$QUEUE_FILE"
    fi

    # Check if session is already active (focused) - skip notification if so
    if "$PYTHON3_PATH" "$SCRIPT_DIR/check_session_active.py" "$SESSION_UUID" 2>/dev/null; then
        # Session already focused, just ring the bell
        echo -e "\a"
        exit 0
    fi

    # Use printf %q to properly escape paths with spaces or special characters
    ESCAPED_SCRIPT="$(printf '%q' "$SCRIPT_DIR/activate_iterm_session.py")"
    ESCAPED_UUID="$(printf '%q' "$SESSION_UUID")"

    terminal-notifier \
        -title "Claude Code" \
        -message "Claude is waiting for your input" \
        -sound Glass \
        -execute "$PYTHON3_PATH $ESCAPED_SCRIPT $ESCAPED_UUID"
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
