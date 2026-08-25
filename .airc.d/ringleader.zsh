# `rl session enrich` / `harvest` shell out to the configured agent CLI, and
# subprocess exec bypasses the `claude` function above — so the credential has
# to already be in rl's own env. sops only, not _agent_sandboxed: rl curates
# ~/.claude and ~/.codex, which no nono agent profile grants.
rl() { sops-exec rl "$@"; }
