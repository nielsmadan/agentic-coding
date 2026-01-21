#!/bin/bash

# Required for Raycast Script Commands
# @raycast.schemaVersion 1
# @raycast.title Next Claude Session
# @raycast.mode silent
# @raycast.icon 🤖

SCRIPT_DIR="$HOME/.claude/hooks"
PYTHON3="$(pyenv which python3 2>/dev/null || command -v python3)"
LOG="/tmp/session_cycle.log"
LOCK="/tmp/session_cycle.lock"

# Log function with millisecond timestamps
log() {
    echo "$(date '+%H:%M:%S.%3N') $1" >> "$LOG"
}

# Acquire lock using mkdir (atomic on POSIX)
LOCKDIR="/tmp/session_cycle.lockdir"
cleanup() { rmdir "$LOCKDIR" 2>/dev/null; }
trap cleanup EXIT

log "=== SHORTCUT PRESSED, waiting for lock ==="
TRIES=0
while ! mkdir "$LOCKDIR" 2>/dev/null; do
    TRIES=$((TRIES + 1))
    if [ $TRIES -gt 20 ]; then  # 2 seconds (20 * 0.1s)
        log "=== LOCK TIMEOUT, skipping ==="
        echo "Busy"
        exit 0
    fi
    sleep 0.1
done
log "Lock acquired"

# Get queue state BEFORE anything
log "-> queue list start"
QUEUE_BEFORE=$("$PYTHON3" "$SCRIPT_DIR/session_queue.py" list | tr '\n' ' ')
log "<- queue list done: $QUEUE_BEFORE"

# Get current session UUID from iTerm2
log "-> iTerm2 current session start"
CURRENT=$("$PYTHON3" -c "
import iterm2
async def main(c):
    app = await iterm2.async_get_app(c)
    w = app.current_terminal_window
    if w and w.current_tab and w.current_tab.current_session:
        print(w.current_tab.current_session.session_id)
iterm2.run_until_complete(main)
" 2>/dev/null)
log "<- iTerm2 current session done: $CURRENT"

# Get first session from queue (simple round-robin)
log "-> queue first start"
FIRST=$("$PYTHON3" "$SCRIPT_DIR/session_queue.py" first)
log "<- queue first done: $FIRST"

if [ -z "$FIRST" ]; then
    log "ERROR: No sessions waiting"
    echo "No sessions waiting"
    exit 0
fi

# Extract UUIDs for comparison
CURRENT_UUID="${CURRENT##*:}"
FIRST_UUID="${FIRST##*:}"

# If first session is current, rotate it and get the new first
if [ "$CURRENT_UUID" = "$FIRST_UUID" ]; then
    log "First == Current, rotating"
    log "-> queue rotate start"
    "$PYTHON3" "$SCRIPT_DIR/session_queue.py" rotate "$FIRST"
    log "<- queue rotate done"
    log "-> queue first start"
    FIRST=$("$PYTHON3" "$SCRIPT_DIR/session_queue.py" first)
    log "<- queue first done: $FIRST"
    if [ -z "$FIRST" ]; then
        log "ERROR: No other sessions"
        echo "No other sessions"
        exit 0
    fi
fi

# Activate the session
log "-> activate_iterm_session start: $FIRST"
"$PYTHON3" "$SCRIPT_DIR/activate_iterm_session.py" "$FIRST"
log "<- activate_iterm_session done"

# Rotate to end of queue
log "-> queue rotate start"
"$PYTHON3" "$SCRIPT_DIR/session_queue.py" rotate "$FIRST"
log "<- queue rotate done"

# Get queue state AFTER
log "-> queue list start"
QUEUE_AFTER=$("$PYTHON3" "$SCRIPT_DIR/session_queue.py" list | tr '\n' ' ')
log "<- queue list done: $QUEUE_AFTER"
log "=== DONE ==="

# Show remaining count
COUNT=$("$PYTHON3" "$SCRIPT_DIR/session_queue.py" count)
echo "$COUNT in queue"
