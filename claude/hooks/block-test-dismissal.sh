#!/bin/bash
# Hook: Stop
# Blocks Claude from stopping when it dismisses test/lint failures
# as "pre-existing", "flaky", "already broken", etc.

input=$(cat)

# Prevent infinite loops — if we already blocked once, let it stop
stop_hook_active=$(echo "$input" | jq -r '.stop_hook_active // false' 2>/dev/null)
if [ "$stop_hook_active" = "true" ]; then
  exit 0
fi

# Get Claude's last message
message=$(echo "$input" | jq -r '.last_assistant_message // ""' 2>/dev/null)
[ -z "$message" ] && exit 0

# Convert to lowercase for matching
msg_lower=$(echo "$message" | tr '[:upper:]' '[:lower:]')

# Check for test/failure context first — avoid false positives
has_test_context=false
if echo "$msg_lower" | grep -qiE 'test|lint|type.?check|typecheck|fail|error|broken|CI'; then
  has_test_context=true
fi

$has_test_context || exit 0

# Check for dismissal patterns
if echo "$msg_lower" | grep -qiE \
  'pre-existing|pre existing|already (broken|failing|failed)|was already|flaky test|'\
'unrelated to (my|our|your|the) changes|not (caused|introduced) by|'\
'(skip|ignore|move on).{0,30}(test|lint|check|fail)|'\
'not.{0,20}(my|our) (fault|problem|issue)|'\
'(test|check).{0,30}(skip|ignore|move on)|'\
'existing (issue|bug|problem|failure)'; then
  # User-approved bypass: if the assistant message contains the exact phrase
  # [user-approved-preexisting], allow the stop through. The phrase should
  # only appear when the user has explicitly told the assistant in the current
  # session that a specific warning / failure is acceptable on this branch.
  if echo "$message" | grep -qF '[user-approved-preexisting]'; then
    exit 0
  fi
  cat << 'EOF'
{"decision": "block", "reason": "You are dismissing test/lint failures instead of fixing them. This is not allowed. Per project policy: ALL checks must pass. 'Pre-existing' is not an excuse — fix every failure now. Run the failing command, read ALL errors, and fix them in one pass."}
EOF
  exit 0
fi

exit 0
