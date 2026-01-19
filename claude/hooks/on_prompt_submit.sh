#!/bin/bash
# Remove session from queues when user submits input

# Debug log
echo "$(date): on_prompt_submit ITERM_SESSION_ID=$ITERM_SESSION_ID" >> /tmp/claude_hook_debug.log

if [ -n "$ITERM_SESSION_ID" ]; then
    PRIMARY_QUEUE="$HOME/.claude_session_queue"
    COMPLETED_QUEUE="$HOME/.claude_completed_queue"

    # Remove from primary queue (waiting for input)
    if [ -f "$PRIMARY_QUEUE" ]; then
        grep -vxF "$ITERM_SESSION_ID" "$PRIMARY_QUEUE" > "$PRIMARY_QUEUE.tmp" && mv "$PRIMARY_QUEUE.tmp" "$PRIMARY_QUEUE"
        echo "$(date): removed from primary queue" >> /tmp/claude_hook_debug.log
    fi

    # Remove from completed queue
    if [ -f "$COMPLETED_QUEUE" ]; then
        grep -vxF "$ITERM_SESSION_ID" "$COMPLETED_QUEUE" > "$COMPLETED_QUEUE.tmp" && mv "$COMPLETED_QUEUE.tmp" "$COMPLETED_QUEUE"
    fi
fi

echo "$(date): on_prompt_submit done" >> /tmp/claude_hook_debug.log
