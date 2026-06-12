#!/bin/bash
# Hook: PreToolUse on WebFetch
# Soft nudge toward the Jina MCP for external web pages. NON-BLOCKING: it only
# injects additionalContext, never denies — so WebFetch always works as a
# fallback when Jina is down, rate-limited, or returns thin content.
#
# Stays quiet (no nudge) when WebFetch is the correct tool per the Web Fetching
# policy in claude/CLAUDE.md: github.com, localhost, and plain data files.

input=$(cat)
url=$(echo "$input" | jq -r '.tool_input.url // ""' 2>/dev/null)

[ -z "$url" ] && exit 0

# WebFetch is already the right call for these — don't nag.
#   - github.com / raw.githubusercontent.com / gist  (sensible HTML already)
#   - localhost / loopback dev servers
#   - plain data formats where Jina adds latency without value
if echo "$url" | grep -qiE '://([^/]*\.)?(github\.com|githubusercontent\.com)|://gist\.github\.com|://(localhost|127\.0\.0\.1|0\.0\.0\.0)([:/]|$)'; then
  exit 0
fi
if echo "$url" | grep -qiE '\.(json|xml|rss|atom|pdf|txt|csv|ya?ml)([?#]|$)|/(json|xml)([?#]|$)'; then
  exit 0
fi

jq -n '{
  hookSpecificOutput: {
    hookEventName: "PreToolUse",
    additionalContext: "Nudge: for external web pages, prefer mcp__jina__read_url (renders JS, returns clean markdown) over WebFetch. WebFetch is fine for plain HTML/feeds/PDF, and is the correct fallback if Jina is unavailable or returns thin content — in that case, proceed with WebFetch."
  }
}'
exit 0
