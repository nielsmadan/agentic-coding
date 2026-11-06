# `rl session enrich` / `harvest` shell out to the configured agent CLI, and
# subprocess exec bypasses the `claude` function above — so the credential has
# to already be in rl's own env. sops only, not _agent_sandboxed: rl curates
# ~/.claude and ~/.codex, which no nono agent profile grants.
#
# bin/rl-launch puts the agent wrappers back in front of the sessions rl resumes;
# a bare `codex` falls back to its own workspace-write Seatbelt with no network.
: ${AC_DIR:=${0:A:h:h}}
rl() { PATH="$AC_DIR/bin/rl-launch:$PATH" sops-exec rl "$@"; }
