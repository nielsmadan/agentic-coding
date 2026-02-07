#!/bin/bash
# Hook: PostToolUseFailure on Bash
# When test/lint/type-check commands fail, inject context reminding Claude
# to fix failures rather than dismissing them as "pre-existing issues."

input=$(cat)
command=$(echo "$input" | jq -r '.tool_input.command // ""' 2>/dev/null)

# Exit silently if we can't parse the command
[ -z "$command" ] && exit 0

# Match common test runners, linters, and type checkers
# Also match package manager scripts with test/lint/check targets
if echo "$command" | grep -qiE \
  '\b(pytest|jest|mocha|vitest|rspec|unittest|cargo test|go test|flutter test|dart test|phpunit)\b|'\
'\b(eslint|prettier.*(--check|--list-different)|flake8|pylint|rubocop|golangci-lint|swiftlint|dart analyze|flutter analyze|biome|oxlint|stylelint|shellcheck)\b|'\
'\b(mypy|pyright|pytype|tsc\b|flow check)\b|'\
'\b(npm|yarn|pnpm|make|rake)\b.*(test|lint|check|typecheck|type-check|analyze)'; then
  cat << 'EOF'
{"additionalContext": "This test/lint/type-check command failed. You MUST fix ALL failures before proceeding. Do NOT dismiss them as pre-existing issues. If something fails after your changes, either your changes caused it or it needs fixing regardless. Fix every failure now."}
EOF
fi
