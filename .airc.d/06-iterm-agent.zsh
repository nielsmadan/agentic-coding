_agent_iterm_run() {
  local recipe=$1 implementation=$2
  shift 2
  if [[ $TERM_PROGRAM != iTerm.app || -z $ITERM_SESSION_ID || -n $AGENT_ITERM_LAUNCH_ACTIVE || ! -t 0 || ! -t 1 ]]; then
    "$implementation" "$@"
    return
  fi
  zmodload zsh/system
  local shell_pid=$sysparams[pid]
  local -x AGENT_ITERM_LAUNCH_ACTIVE=1
  local -a options=()
  [[ -n $AGENT_FORCE_SANDBOX || -n $AGENT_REQUIRE_SANDBOX ]] && options+=(--force-sandbox)
  local token result
  token=$(iterm-agent-register start "$recipe" --pid "$shell_pid" "${options[@]}") || token=
  {
    "$implementation" "$@"
  } always {
    result=$?
    [[ -z $token ]] || iterm-agent-register end "$token" --exit-status "$result"
  }
}
