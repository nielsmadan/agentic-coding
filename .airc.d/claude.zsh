# Claude Code aliases

# bellhop's relay lets callboard ring the session. It is passed here because loadout's
# mcp.toml cannot yet give a server to Claude alone. The = form matters: --mcp-config
# is variadic and would swallow a following subcommand or prompt.
_claude_mcp_args() {
  local relay="${XDG_CONFIG_HOME:-$HOME/.config}/bellhop/bellhop-mcp.json"
  reply=()
  [[ -r $relay ]] && reply=("--mcp-config=$relay")
}

_claude_launch() {
  if _agent_raw_dir; then
    print -u2 -r -- "claude: unsandboxed (${PWD:A})"
    claude-raw "$@"
    return
  fi
  # claude-local cannot read ~/.config/bellhop, and Claude refuses to start on an unreadable --mcp-config.
  local -a reply=()
  _agent_unsandboxed_profile && _claude_mcp_args
  AGENT_HARNESS=claude _agent_sandboxed claude-local claude "${reply[@]}" "$@"
}

# Escape hatch: unsandboxed. For `loadout sync`, ~/ac and ~/rc work, and anything
# that must write outside ~/wrksp.
_claude_raw_launch() {
  local -a reply
  _claude_mcp_args
  AGENT_HARNESS=claude sops-exec claude "${reply[@]}" "$@"
}

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

# Claude Code against OpenRouter. No sops-exec fallback on purpose: falling
# through to a bare `claude` would silently bill the subscription instead.
# The tier aliases are remapped cheap->strong so /model haiku|sonnet|opus
# switches models mid-session. [1m] declares the real 1M context window.
_clor_launch() {
  local start="${CLOR_MODEL:-sonnet}"
  local effort="${CLOR_EFFORT:-high}"
  local -a launch=(nono run -p claude-local -- claude)
  local sandbox_env="AGENT_SANDBOX=1 AGENT_SANDBOX_PROFILE=claude-local"
  if _agent_unsandboxed_profile; then
    launch=(claude)
    sandbox_env=
  fi
  sops exec-env "$SOPS_SECRETS" \
"ANTHROPIC_BASE_URL=https://openrouter.ai/api \
ANTHROPIC_API_KEY=\$OPENROUTER_API_KEY \
ANTHROPIC_AUTH_TOKEN= \
CLAUDE_CODE_OAUTH_TOKEN= \
ANTHROPIC_DEFAULT_HAIKU_MODEL='openai/gpt-6-luna[1m]' \
ANTHROPIC_DEFAULT_SONNET_MODEL='meta/muse-ember[1m]' \
ANTHROPIC_DEFAULT_OPUS_MODEL='openai/gpt-6.1-sol[1m]' \
CLAUDE_CODE_SUBAGENT_MODEL='meta/muse-ember[1m]' \
CLAUDE_CODE_ALWAYS_ENABLE_EFFORT=1 \
CLAUDE_CODE_EFFORT_LEVEL=$(printf '%q' "$effort") \
CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1 \
AGENT_HARNESS=claude \
DOCKER_HOST=unix://$HOME/.colima/default/docker.sock \
$sandbox_env \
$(printf '%q ' "${launch[@]}") --model $(printf '%q' "$start") --permission-mode acceptEdits $(printf '%q ' "$@")"
}

claude() {
  local preset
  if preset=$(_agent_model_tier anthropic "${1:-}"); then
    shift
    set -- --model "${preset%:*}" --effort "${preset##*:}" "$@"
  fi
  _agent_iterm_run claude _claude_launch "$@"
}

claude-raw() { _agent_iterm_run claude-raw _claude_raw_launch "$@"; }

clor() { _agent_iterm_run clor _clor_launch "$@"; }
