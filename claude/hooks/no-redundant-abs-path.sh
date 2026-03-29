#!/bin/bash
# Hook: PreToolUse on Bash
# Block commands that use absolute paths when they could use relative paths
# from the current working directory.

input=$(cat)
command=$(echo "$input" | jq -r '.tool_input.command // ""' 2>/dev/null)
cwd=$(echo "$input" | jq -r '.cwd // ""' 2>/dev/null)

[ -z "$command" ] && exit 0
[ -z "$cwd" ] && exit 0

# Skip very short cwds to avoid false positives
if [ ${#cwd} -lt 10 ]; then
  exit 0
fi

# Check if command contains the cwd
# Use a fixed-string grep to avoid regex issues with special chars in paths
if echo "$command" | grep -qF "${cwd}"; then
  echo "BLOCKED: You are already in ${cwd}. Use relative paths instead of absolute paths, and drop flags like 'git -C' that point here." >&2
  exit 2
fi

exit 0
