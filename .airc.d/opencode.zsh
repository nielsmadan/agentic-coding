# OpenCode aliases
# No -raw variant: opencode is never run outside the sandbox.
#
# nono writes an ~80-line capability banner to stderr before exec'ing the child,
# and opencode's redraw does not reclaim it, so it shows through the scroll area.
# The sh shim clears the visible screen from inside the sandbox — after the
# banner, before opencode draws. nono's exit summary survives because it prints
# after the child exits, which `--silent` would have suppressed along with the
# banner. Deliberately not \033[3J: that clears the scrollback the user had
# before launching, and the banner is worth keeping there.
opencode() {
  AGENT_HARNESS=opencode _agent_sandboxed opencode-local \
    /bin/sh -c 'printf "\033[2J\033[H"; exec "$@"' sh opencode "$@"
}

alias oc="opencode"
alias ocs="opencode -m openrouter/qwen/qwen3.8-2.4t-a95b"
alias occo="opencode --continue"
alias occof="opencode --continue --fork"

# OpenCode scans ~/.claude/skills and .claude/skills as well as its own, and
# resolves a duplicate name by race — skill/index.ts loads every SKILL.md under
# `concurrency: "unbounded"` and assigns into one name-keyed map, warning on a
# collision without returning, so whichever read finishes last wins. loadout
# writes a per-harness flavour of every skill to both roots, so without this each
# session gets one or the other at random. See loadout docs/reference/opencode.md.
export OPENCODE_DISABLE_CLAUDE_CODE_SKILLS=1
