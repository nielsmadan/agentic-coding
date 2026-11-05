# The first agent-device command starts the shared daemon, which then serves every
# agent with this shell's permissions. Outside the sandbox, start the sandboxed one
# first so this command reuses it instead of starting an unsandboxed daemon.
agent-device() {
  if [[ -z $AGENT_SANDBOX ]] && (( $+commands[nono] && $+commands[agent-device-daemon] )); then
    agent-device-daemon ensure >/dev/null || {
      print -u2 "agent-device: could not start the sandboxed daemon; see agent-device-daemon ensure"
      return 1
    }
  fi
  command agent-device "$@"
}
