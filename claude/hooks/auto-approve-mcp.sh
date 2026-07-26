#!/bin/bash
# Hook: PermissionRequest — auto-approve canonically allowed MCP tools.

input=$(cat)
tool=$(echo "$input" | jq -r '.tool_name // ""' 2>/dev/null)
cwd=$(echo "$input" | jq -r '.cwd // .tool_input.cwd // ""' 2>/dev/null)

[[ "$tool" == mcp__* ]] || exit 0

files=("$HOME/.claude/mcp-permissions.json")
if [[ -n "$cwd" ]]; then
  files+=("$cwd/.aiconf/mcp-permissions.json")
fi

policy='{"allow":[],"ask":[],"deny":[]}'
for file in "${files[@]}"; do
  [[ -f "$file" ]] || continue
  policy=$(jq -s '
    {
      allow: (.[0].allow + .[1].allow | unique),
      ask: (.[0].ask + .[1].ask | unique),
      deny: (.[0].deny + .[1].deny | unique)
    }
  ' <(printf '%s\n' "$policy") "$file" 2>/dev/null) || exit 0
done

decision=$(jq -r --arg tool "$tool" '
  def native:
    sub("/"; "__") | sub("/"; "__") | "mcp__" + .;
  def matches($target):
    if ($target | endswith("/*"))
    then $tool | startswith(($target | native | sub("\\*$"; "")))
    else $tool == ($target | native)
    end;
  if any(.deny[]; matches(.)) or any(.ask[]; matches(.)) then "no"
  elif any(.allow[]; matches(.)) then "yes"
  else "no"
  end
' <<<"$policy" 2>/dev/null)

[[ "$decision" == "yes" ]] || exit 0

jq -n '{
  hookSpecificOutput: {
    hookEventName: "PermissionRequest",
    decision: { behavior: "allow" }
  }
}'
