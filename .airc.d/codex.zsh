# Codex applies its own Seatbelt sandbox per command, and Seatbelt cannot nest:
# inside nono, `workspace-write` fails every command with
# `sandbox-exec: sandbox_apply: Operation not permitted`. Overridden per
# invocation rather than in config.toml so codex-raw keeps its own sandbox.
#
# approval_policy is per-invocation for the same reason: nono is the boundary
# here, so the prompt only adds friction, while codex-raw keeps on-request from
# config.toml because nothing contains it there.
codex() {
  if _agent_raw_dir; then
    print -u2 -r -- "codex: unsandboxed (${PWD:A})"
    codex-raw "$@"
    return
  fi
  AGENT_HARNESS=codex _agent_sandboxed codex-local codex -c sandbox_mode='"danger-full-access"' -c approval_policy='"never"' "$@"
}
codex-raw() { AGENT_HARNESS=codex _sops_exec codex "$@"; }

alias cxco="codex resume --last"
alias cxcof="codex fork --last"

alias cxco-raw="codex-raw resume --last"
alias cxcof-raw="codex-raw fork --last"
