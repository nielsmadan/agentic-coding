#!/bin/bash
# Hook: PreToolUse on Bash
# Block git -C <path> when <path> resolves to the current working directory.

input=$(cat)
command=$(echo "$input" | jq -r '.tool_input.command // ""' 2>/dev/null)

[ -z "$command" ] && exit 0

# Extract the path after git -C (handles both quoted and unquoted)
git_c_path=$(echo "$command" | grep -oE '\bgit[[:space:]]+-C[[:space:]]+("([^"]+)"|'\''([^'\'']+)'\''|[^ ]+)' | head -1 | sed -E 's/^git[[:space:]]+-C[[:space:]]+//; s/^["'\''"]//; s/["'\''"]$//')

[ -z "$git_c_path" ] && exit 0

# Resolve both paths to absolute
resolved_path=$(cd "$git_c_path" 2>/dev/null && pwd -P)
current_dir=$(pwd -P)

[ -z "$resolved_path" ] && exit 0

if [ "$resolved_path" = "$current_dir" ]; then
  echo "BLOCKED: You are already in $current_dir. Drop the '-C $git_c_path' flag and run the git command directly." >&2
  exit 2
fi

exit 0
