# Claude Code aliases

# claude runs inside the nono sandbox (profile: nono/claude-local.json). Defined
# here rather than in ~/rc/.zshrc alongside codex/pi/opencode because it is agent
# tooling — but that means ~/rc/.zshrc must NOT also define claude(): it sources
# ~/.airc first and would otherwise override this.
#
# DOCKER_HOST is explicit because ~/.docker/config.json sits in nono's permanent
# deny group, so docker cannot read its context and falls back to a socket colima
# does not create.
claude() {
  if command -v nono >/dev/null 2>&1 && [ -f "$HOME/.config/nono/profiles/claude-local.json" ]; then
    DOCKER_HOST="unix://$HOME/.colima/default/docker.sock" \
      _sops_exec nono run -p claude-local -- claude "$@"
  else
    _sops_exec claude "$@"
  fi
}

# Escape hatch: unsandboxed. For `loadout sync`, ~/ac and ~/rc work, and anything
# that must write outside ~/wrksp.
claude-raw() { _sops_exec claude "$@"; }

alias clco="claude --continue"

clcof() {
  local name
  name="$(command clcof)" || return
  claude --continue --fork-session --name "$name" "$@"
}

_ccone() { claude -p "$*"; }
alias ccone="noglob _ccone"

# Claude Code against OpenRouter. No _sops_exec fallback on purpose: falling
# through to a bare `claude` would silently bill the subscription instead.
# The tier aliases are remapped cheap->strong so /model haiku|sonnet|opus
# switches models mid-session. [1m] declares the real 1M context window.
clor() {
  local start="${CLOR_MODEL:-haiku}"
  local effort="${CLOR_EFFORT:-high}"
  sops exec-env "$SOPS_SECRETS" \
"ANTHROPIC_BASE_URL=https://openrouter.ai/api \
ANTHROPIC_API_KEY=\$OPENROUTER_API_KEY \
ANTHROPIC_AUTH_TOKEN= \
CLAUDE_CODE_OAUTH_TOKEN= \
ANTHROPIC_DEFAULT_HAIKU_MODEL='deepseek/deepseek-v4-flash-0731[1m]' \
ANTHROPIC_DEFAULT_SONNET_MODEL='meta/muse-spark-1.2[1m]' \
ANTHROPIC_DEFAULT_OPUS_MODEL='moonshotai/kimi-k3[1m]' \
CLAUDE_CODE_SUBAGENT_MODEL='deepseek/deepseek-v4-flash-0731[1m]' \
CLAUDE_CODE_ALWAYS_ENABLE_EFFORT=1 \
CLAUDE_CODE_EFFORT_LEVEL=$(printf '%q' "$effort") \
CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1 \
DOCKER_HOST=unix://$HOME/.colima/default/docker.sock \
nono run -p claude-local -- claude --model $(printf '%q' "$start") --permission-mode acceptEdits $(printf '%q ' "$@")"
}
