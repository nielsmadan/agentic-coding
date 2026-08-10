# No -raw variant: pi is never run outside the sandbox.
pi() { _agent_sandboxed pi-local pi "$@"; }

alias pico="pi --continue"

picof() {
  local session
  session="$(command picof)" || return
  pi --fork "$session" "$@"
}
