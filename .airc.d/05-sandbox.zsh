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
#
# bin/sandbox-shims holds wrappers for tools whose inner-sandbox switch is an
# NSUserDefault rather than an env var, so argv is the only channel. Only the
# sandbox wrapper prepends it; 00-path.zsh puts bin/ alone on the interactive
# PATH, which keeps the shims off the user's own shell.
#
# DISABLE_AUTOUPDATER keeps Claude Code from nagging about an update it cannot
# install: ~/.local/share/claude and the ~/.local/bin/claude symlink are read-only
# here on purpose, since claude-raw executes whatever that symlink resolves to.
# claude-raw picks the update up instead.
#
# VHS_NO_SANDBOX makes vhs pass --no-sandbox to the Chrome it drives; without it
# recording dies at `could not open ttyd`. Chrome additionally needs the
# com.google.Chrome. mach-register rule in nono/agent-common.json — both are
# required, neither is sufficient alone.
#
# Working in these repos means writing outside ~/wrksp (loadout sync, these
# wrappers themselves), which the sandbox exists to prevent — so claude and codex
# route to their -raw variant here. AGENT_FORCE_SANDBOX=1 overrides. pi and
# opencode have no raw variant and are unaffected.
AGENT_RAW_DIRS=("$HOME/ac" "$HOME/rc")

_agent_raw_dir() {
  [[ -n $AGENT_FORCE_SANDBOX ]] && return 1
  local dir here=${PWD:A}
  for dir in "${AGENT_RAW_DIRS[@]}"; do
    dir=${dir:A}
    [[ $here == $dir || $here == $dir/* ]] && return 0
  done
  return 1
}

_agent_sandboxed() {
  local profile=$1 cmd=$2
  shift 2
  if command -v nono >/dev/null 2>&1 && [ -f "$HOME/.config/nono/profiles/$profile.json" ]; then
    PATH="$HOME/ac/bin/sandbox-shims:$HOME/ac/bin:$PATH" \
    AGENT_SANDBOX=1 \
    DOCKER_HOST="unix://$HOME/.colima/default/docker.sock" \
    OTHER_SWIFT_FLAGS='$(inherited) -disable-sandbox' \
    AGENT_BROWSER_ARGS=--no-sandbox \
    VHS_NO_SANDBOX=true \
    DISABLE_AUTOUPDATER=1 \
      _sops_exec nono run -p "$profile" -- "$cmd" "$@"
  else
    _sops_exec "$cmd" "$@"
  fi
}
