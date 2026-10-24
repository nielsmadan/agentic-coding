# OpenCode aliases
# No -raw variant: opencode is never run outside the sandbox.
# OpenCode 2 otherwise hands tool execution to a shared background server that
# may live outside this sandbox; --standalone keeps a private one inside it.
# Only the TUI, run and mini accept it.
opencode() {
  local -a args=("$@")
  case $1 in
    run|mini) args=("$1" --standalone "${@:2}") ;;
    -*|'') args=(--standalone "$@") ;;
    *) [[ -d $1 ]] && args=(--standalone "$@") ;;
  esac
  AGENT_HARNESS=opencode _agent_sandboxed opencode-local opencode "${args[@]}"
}

alias oc="opencode"
# The OpenCode 2 TUI has no --model flag.
alias ocs='OPENCODE_CONFIG_CONTENT='\''{"model":"openrouter/meta/muse-spark-1.3"}'\'' opencode'
alias occof="opencode --continue --fork"

# OpenCode scans ~/.claude/skills and .claude/skills as well as its own, and
# resolves a duplicate name by race — skill/index.ts loads every SKILL.md under
# `concurrency: "unbounded"` and assigns into one name-keyed map, warning on a
# collision without returning, so whichever read finishes last wins. loadout
# writes a per-harness flavour of every skill to both roots, so without this each
# session gets one or the other at random. See loadout docs/reference/opencode.md.
export OPENCODE_DISABLE_CLAUDE_CODE_SKILLS=1
