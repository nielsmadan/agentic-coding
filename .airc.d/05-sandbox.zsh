# Agent CLIs run inside the nono sandbox, with sops-injected secrets.
#
# These wrappers live here rather than in ~/rc/.zshrc because they are agent
# tooling — but that means ~/rc/.zshrc must NOT also define them: it sources
# ~/.airc first and would otherwise override every one.
#
# DOCKER_HOST is explicit because ~/.docker/config.json sits in nono's permanent
# deny group, so docker cannot read its context and falls back to a socket colima
# does not create.
_agent_sandboxed() {
  local profile=$1 cmd=$2
  shift 2
  if command -v nono >/dev/null 2>&1 && [ -f "$HOME/.config/nono/profiles/$profile.json" ]; then
    DOCKER_HOST="unix://$HOME/.colima/default/docker.sock" \
      _sops_exec nono run -p "$profile" -- "$cmd" "$@"
  else
    _sops_exec "$cmd" "$@"
  fi
}
