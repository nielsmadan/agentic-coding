# Claude Code aliases
alias clco="claude --continue"

clcof() {
  local name
  name="$(command clcof)" || return
  claude --continue --fork-session --name "$name" "$@"
}

_ccone() { claude -p "$*"; }
alias ccone="noglob _ccone"
