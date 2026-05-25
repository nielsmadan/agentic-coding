_todo() {
  if ! git rev-parse --show-toplevel >/dev/null 2>&1 || [[ "$(pwd)" != "$(git rev-parse --show-toplevel)" ]]; then
    echo "Error: must be in a git repo root directory" >&2
    return 1
  fi
  local interactive=false skill_flags=""
  if [[ "$1" == -* && "$1" != --* ]]; then
    local flags="$1"; shift
    [[ "$flags" == *i* ]] && { interactive=true; skill_flags+="-i "; }
    [[ "$flags" == *c* ]] && skill_flags+="-c "
  fi
  if $interactive; then
    claude "/todo ${skill_flags}$*"
  else
    local prompt="/todo ${skill_flags}$*"
    echo "$prompt" | claude -p --disallowedTools AskUserQuestion > /tmp/todo-last.log 2>&1 &
    disown 2>/dev/null
    echo "Todo queued (pid $!)"
  fi
}
alias todo="noglob _todo"
