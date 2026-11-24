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
_codex_launch() {
  local -a reply
  _codex_command
  if _agent_unsandboxed_profile; then
    AGENT_HARNESS=codex sops-exec "${reply[@]}" "$@"
    return
  fi
  if _agent_raw_dir; then
    print -u2 -r -- "codex: unsandboxed (${PWD:A})"
    codex-raw "$@"
    return
  fi
  AGENT_HARNESS=codex _agent_sandboxed codex-local "${reply[@]}" -c sandbox_mode='"danger-full-access"' -c approval_policy='"never"' "$@"
}
_codex_raw_launch() { local -a reply; _codex_command; AGENT_HARNESS=codex sops-exec "${reply[@]}" -s danger-full-access "$@"; }

# Juggler reads the terminal from the env of the app server that runs the hooks, so
# each session needs its own server, started from its terminal and inside its
# sandbox. `bellhop codex` starts one that bellhop can also reach; without bellhop,
# --no-daemon keeps it in-process.
_codex_command() {
  if (( $+commands[bellhop] )); then
    reply=(bellhop codex)
  else
    reply=(codex --no-daemon)
  fi
}

alias cxcof="codex fork --last"

alias cxco-raw="codex-raw resume --last"
alias cxcof-raw="codex-raw fork --last"

codex() {
  local preset
  if preset=$(_agent_model_tier openai "${1:-}"); then
    shift
    set -- --model "${preset%:*}" -c "model_reasoning_effort=\"${preset##*:}\"" "$@"
  fi
  _agent_iterm_run codex _codex_launch "$@"
}

codex-raw() { _agent_iterm_run codex-raw _codex_raw_launch "$@"; }
