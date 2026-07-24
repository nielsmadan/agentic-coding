alias pico="pi --continue"

picof() {
  local session
  session="$(command picof)" || return
  pi --fork "$session" "$@"
}
