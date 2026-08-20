# Claude Code aliases

claude() {
  if _agent_raw_dir; then
    print -u2 -r -- "claude: unsandboxed (${PWD:A})"
    claude-raw "$@"
    return
  fi
  AGENT_HARNESS=claude _agent_sandboxed claude-local claude "$@"
}

# Escape hatch: unsandboxed. For `loadout sync`, ~/ac and ~/rc work, and anything
# that must write outside ~/wrksp.
claude-raw() { AGENT_HARNESS=claude _sops_exec claude "$@"; }

alias clco="claude --continue"
alias clco-raw="claude-raw --continue"

clcof() {
  local name
  name="$(command clcof)" || return
  claude --continue --fork-session --name "$name" "$@"
}

clcof-raw() {
  local name
  name="$(command clcof)" || return
  claude-raw --continue --fork-session --name "$name" "$@"
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
ANTHROPIC_DEFAULT_HAIKU_MODEL='deepseek/deepseek-v4-pro-0813[1m]' \
ANTHROPIC_DEFAULT_SONNET_MODEL='meta/muse-spark-1.2[1m]' \
ANTHROPIC_DEFAULT_OPUS_MODEL='z-ai/glm-5.3[1m]' \
CLAUDE_CODE_SUBAGENT_MODEL='deepseek/deepseek-v4-pro-0813[1m]' \
CLAUDE_CODE_ALWAYS_ENABLE_EFFORT=1 \
CLAUDE_CODE_EFFORT_LEVEL=$(printf '%q' "$effort") \
CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1 \
AGENT_HARNESS=claude \
DOCKER_HOST=unix://$HOME/.colima/default/docker.sock \
nono run -p claude-local -- claude --model $(printf '%q' "$start") --permission-mode acceptEdits $(printf '%q ' "$@")"
}
