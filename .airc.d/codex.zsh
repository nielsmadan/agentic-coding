# Codex applies its own Seatbelt sandbox per command, and Seatbelt cannot nest:
# inside nono, `workspace-write` fails every command with
# `sandbox-exec: sandbox_apply: Operation not permitted`. Overridden per
# invocation rather than in config.toml so codex-raw keeps its own sandbox.
codex() { _agent_sandboxed codex-local codex -c sandbox_mode='"danger-full-access"' "$@"; }
codex-raw() { _sops_exec codex "$@"; }

alias cxco="codex resume --last"
alias cxcof="codex fork --last"

alias cxco-raw="codex-raw resume --last"
alias cxcof-raw="codex-raw fork --last"
