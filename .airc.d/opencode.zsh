# OpenCode aliases
# No -raw variant: opencode is never run outside the sandbox.
opencode() { AGENT_HARNESS=opencode _agent_sandboxed opencode-local opencode "$@"; }

alias oc="opencode"
alias ocs="opencode -m openrouter/moonshotai/kimi-k3"
alias occo="opencode --continue"
alias occof="opencode --continue --fork"

# OpenCode scans ~/.claude/skills and .claude/skills as well as its own, and
# resolves a duplicate name by race — skill/index.ts loads every SKILL.md under
# `concurrency: "unbounded"` and assigns into one name-keyed map, warning on a
# collision without returning, so whichever read finishes last wins. loadout
# writes a per-harness flavour of every skill to both roots, so without this each
# session gets one or the other at random. See loadout docs/reference/opencode.md.
export OPENCODE_DISABLE_CLAUDE_CODE_SKILLS=1
