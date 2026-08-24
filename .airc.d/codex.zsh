# Codex applies its own Seatbelt sandbox per command, and Seatbelt cannot nest:
# inside nono, `workspace-write` fails every command with
# `sandbox-exec: sandbox_apply: Operation not permitted`. Both wrappers override
# it per invocation rather than in config.toml, so a bare `codex` outside them
# keeps workspace-write.
#
# codex-raw disables it too: the dirs that route to raw are the ones whose work
# writes outside the workspace, which workspace-write blocks. approval_policy
# stays on-request there — with no nono and no Seatbelt, the prompt is the only
# guard left, whereas the sandboxed path drops it because nono is the boundary.
codex() {
  if _agent_raw_dir; then
    print -u2 -r -- "codex: unsandboxed (${PWD:A})"
    codex-raw "$@"
    return
  fi
  AGENT_HARNESS=codex _agent_sandboxed codex-local codex -c sandbox_mode='"danger-full-access"' -c approval_policy='"never"' "$@"
}
codex-raw() { AGENT_HARNESS=codex _sops_exec codex -c sandbox_mode='"danger-full-access"' "$@"; }

alias cxco="codex resume --last"
alias cxcof="codex fork --last"

alias cxco-raw="codex-raw resume --last"
alias cxcof-raw="codex-raw fork --last"
