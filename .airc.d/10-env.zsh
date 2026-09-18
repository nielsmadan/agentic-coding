# Disable Claude Code feedback prompts
export CLAUDE_CODE_DISABLE_FEEDBACK_SURVEY=1

# Claude's config directory. Set explicitly to its own default so that
# ~/.claude.json moves inside it: Claude writes that file by creating
# ~/.claude.json.tmp.<random> and renaming, and a random suffix in $HOME matches
# no grant, so the write is denied in the sandbox (nono#1481). Inside ~/.claude
# the directory grant covers it. Exported globally, not in the sandbox wrapper,
# so `claude` and `claude-raw` read the same store.
#
# The unsandboxed profile skips it: with no nono there is no denied rename, and
# launchd-spawned agents get no shell config, so exporting it here would split
# the store — an onboarded ~/.claude.json for them, an empty
# ~/.claude/.claude.json for interactive sessions, which onboards from scratch.
_agent_unsandboxed_profile || export CLAUDE_CONFIG_DIR="$HOME/.claude"

# nono is the main machine's boundary only. On an unsandboxed machine mise must
# not install it either — the tool is declared in ~/rc's shared config, so the
# opt-out is here rather than there. The full backend spec is required;
# MISE_DISABLE_TOOLS=nono does not match.
if _agent_unsandboxed_profile; then
  export MISE_DISABLE_TOOLS="github:nolabs-ai/nono"
fi
