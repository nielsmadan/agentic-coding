# Cursor CLI. No nolabs-ai pack exists for it, so nono/cursor-local.json is
# written from scratch. The installer links both `cursor-agent` and `agent`, so
# both are wrapped; an unwrapped `agent` would run outside the sandbox.
#
# No -raw variant. Its interactive login lives in the macOS login keychain,
# denied on purpose, so runs authenticate with CURSOR_API_KEY from the sops
# store, and the profile sets AGENT_CLI_CREDENTIAL_STORE=memory so nothing is
# persisted to the keychain or to ~/.cursor/auth.json.
_cursor_model_preset() {
  local tier=${1:-}
  local -A models=(
    haiku claude-haiku-5-5-thinking-high
    sonnet claude-sonnet-5-5-medium
    opus claude-opus-5-5-high
  )
  [[ -n $tier && -n ${models[$tier]} ]] || return 1
  print -r -- "${models[$tier]}"
}

_cursor_agent() {
  local model
  if model=$(_cursor_model_preset "${1:-}"); then
    shift
    set -- --model "$model" "$@"
  fi
  AGENT_HARNESS=cursor _agent_sandboxed cursor-local cursor-agent "$@"
}
cursor-agent() { _cursor_agent "$@"; }
agent() { _cursor_agent "$@"; }
