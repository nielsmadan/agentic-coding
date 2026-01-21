#!/bin/bash

# Required for Raycast Script Commands
# @raycast.schemaVersion 1
# @raycast.title Next Claude Session
# @raycast.mode silent
# @raycast.icon 🤖

SCRIPT_DIR="$HOME/.claude/hooks"
PYTHON3="$(pyenv which python3 2>/dev/null || command -v python3)"

# Get current session UUID from iTerm2
CURRENT=$("$PYTHON3" -c "
import iterm2
async def main(c):
    app = await iterm2.async_get_app(c)
    w = app.current_terminal_window
    if w and w.current_tab and w.current_tab.current_session:
        print(w.current_tab.current_session.session_id)
iterm2.run_until_complete(main)
" 2>/dev/null)

# Get next session from queue
NEXT=$("$PYTHON3" "$SCRIPT_DIR/session_queue.py" next "$CURRENT")

if [ -z "$NEXT" ]; then
    echo "No sessions waiting"
    exit 0
fi

# Activate the session
"$PYTHON3" "$SCRIPT_DIR/activate_iterm_session.py" "$NEXT"

# Rotate to end of queue
"$PYTHON3" "$SCRIPT_DIR/session_queue.py" rotate "$NEXT"

# Show remaining count
COUNT=$("$PYTHON3" "$SCRIPT_DIR/session_queue.py" count)
echo "$COUNT in queue"
