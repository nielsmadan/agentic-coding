#!/bin/bash
# Hook: PreToolUse on WebFetch
# WebFetch is the default per the Web Search & Fetching policy in claude/CLAUDE.md,
# so this stays silent for almost every URL. It only fires on the two hosts that
# block WebFetch outright, where the call is a guaranteed wasted round trip.
# NON-BLOCKING: it injects additionalContext, never denies.

input=$(cat)
url=$(echo "$input" | jq -r '.tool_input.url // ""' 2>/dev/null)

[ -z "$url" ] && exit 0

if echo "$url" | grep -qiE '://([^/]*\.)?(stackoverflow\.com|stackexchange\.com|reddit\.com)([:/]|$)'; then
  jq -n '{
    hookSpecificOutput: {
      hookEventName: "PreToolUse",
      additionalContext: "This host blocks WebFetch. Use `jina-fetch <url> \"<what to extract>\"` instead — this call will fail."
    }
  }'
fi

exit 0
