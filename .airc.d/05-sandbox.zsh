# Agent CLIs run inside the nono sandbox, with sops-injected secrets.
#
# These wrappers live here rather than in ~/rc/.zshrc because they are agent
# tooling — but that means ~/rc/.zshrc must NOT also define them: it sources
# ~/.airc first and would otherwise override every one.
#
# DOCKER_HOST is explicit because ~/.docker/config.json sits in nono's permanent
# deny group, so docker cannot read its context and falls back to a socket colima
# does not create.
#
# OTHER_SWIFT_FLAGS disables swiftc's macro-plugin sandbox: Seatbelt cannot nest,
# so it fails with `sandbox_apply: Operation not permitted` inside nono. Set here
# rather than in each project so contributors are unaffected. xcodebuild also
# needs -IDEPackageSupportDisableManifestSandbox=1 and
# -IDEPackageSupportDisablePluginExecutionSandbox=1, which are NSUserDefaults and
# cannot come from the environment.
_agent_sandboxed() {
  local profile=$1 cmd=$2
  shift 2
  if command -v nono >/dev/null 2>&1 && [ -f "$HOME/.config/nono/profiles/$profile.json" ]; then
    DOCKER_HOST="unix://$HOME/.colima/default/docker.sock" \
    OTHER_SWIFT_FLAGS='$(inherited) -disable-sandbox' \
    AGENT_BROWSER_ARGS=--no-sandbox \
      _sops_exec nono run -p "$profile" -- "$cmd" "$@"
  else
    _sops_exec "$cmd" "$@"
  fi
}
