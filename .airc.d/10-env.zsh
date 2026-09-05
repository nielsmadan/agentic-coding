# Disable Claude Code feedback prompts
export CLAUDE_CODE_DISABLE_FEEDBACK_SURVEY=1

# Claude's config directory. Set explicitly to its own default so that
# ~/.claude.json moves inside it: Claude writes that file by creating
# ~/.claude.json.tmp.<random> and renaming, and a random suffix in $HOME matches
# no grant, so the write is denied in the sandbox (nono#1481). Inside ~/.claude
# the directory grant covers it. Exported globally, not in the sandbox wrapper,
# so `claude` and `claude-raw` read the same store.
export CLAUDE_CONFIG_DIR="$HOME/.claude"
