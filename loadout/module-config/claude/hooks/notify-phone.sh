#!/bin/bash
# Hook: Notification. Pushes to PHONE_NOTIFY_URL (an ntfy topic URL) when a Claude
# session running in tmux waits for input and the Mac has been idle for PHONE_NOTIFY_IDLE seconds (default 120).

[ -n "$PHONE_NOTIFY_URL" ] && [ -n "$TMUX" ] || exit 0

idle=$(ioreg -c IOHIDSystem 2>/dev/null | awk '/HIDIdleTime/ {print int($NF / 1000000000); exit}')
[ -n "$idle" ] && [ "$idle" -lt "${PHONE_NOTIFY_IDLE:-120}" ] && exit 0

input=$(cat)
message=$(jq -r '.message // "Claude needs your input"' <<<"$input")
project=$(basename "$(jq -r '.cwd // "?"' <<<"$input")")
session=$(tmux display-message -p '#S' 2>/dev/null)

curl -fsS -m 5 -H "Title: ${project} (tmux: ${session:-?})" -H "Tags: robot" \
  -d "$message" "$PHONE_NOTIFY_URL" >/dev/null 2>&1

exit 0
