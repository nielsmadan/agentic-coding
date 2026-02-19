#!/bin/bash
# Hook: PreToolUse on Bash
# Redirect gh api calls to dedicated subcommands when alternatives exist.

input=$(cat)
command=$(echo "$input" | jq -r '.tool_input.command // ""' 2>/dev/null)

[ -z "$command" ] && exit 0

# Only check commands containing "gh api"
echo "$command" | grep -qE '\bgh\s+api\b' || exit 0

# Issue comments: gh api repos/{owner}/{repo}/issues/{num}/comments
if echo "$command" | grep -qE 'repos/[^/]+/[^/]+/issues/[0-9]+/comments'; then
  echo "BLOCKED: Use 'gh issue view <num> --comments -R <owner/repo>' instead of gh api for issue comments." >&2
  exit 2
fi

# PR comments: gh api repos/{owner}/{repo}/pulls/{num}/comments
if echo "$command" | grep -qE 'repos/[^/]+/[^/]+/pulls/[0-9]+/comments'; then
  echo "BLOCKED: Use 'gh pr view <num> --comments -R <owner/repo>' instead of gh api for PR comments." >&2
  exit 2
fi

# PR reviews: gh api repos/{owner}/{repo}/pulls/{num}/reviews
if echo "$command" | grep -qE 'repos/[^/]+/[^/]+/pulls/[0-9]+/reviews'; then
  echo "BLOCKED: Use 'gh pr view <num> --json reviews -R <owner/repo>' instead of gh api for PR reviews." >&2
  exit 2
fi

# Releases: gh api repos/{owner}/{repo}/releases
if echo "$command" | grep -qE 'repos/[^/]+/[^/]+/releases'; then
  echo "BLOCKED: Use 'gh release list -R <owner/repo>' instead of gh api for releases." >&2
  exit 2
fi

# Workflow runs: gh api repos/{owner}/{repo}/actions/runs
if echo "$command" | grep -qE 'repos/[^/]+/[^/]+/actions/runs'; then
  echo "BLOCKED: Use 'gh run list -R <owner/repo>' instead of gh api for workflow runs." >&2
  exit 2
fi

# All other gh api calls pass through (commits, GraphQL, etc.)
exit 0
