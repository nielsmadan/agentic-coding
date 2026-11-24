# No -raw variant: pi is never run outside the sandbox.
pi() { AGENT_HARNESS=pi _agent_sandboxed pi-local pi "$@"; }

_pix_default_preset() { print -r -- 'gpt-6.2-sol:max'; }

# Subscription-backed Codex model; plain `pi` keeps the Token Pass default.
# --provider stops a missing ChatGPT login from resolving the id on OpenRouter.
pix() {
  local preset
  if preset=$(_agent_model_tier openai "${1:-}"); then
    shift
  else
    preset=$(_pix_default_preset)
  fi
  pi --provider openai --model "$preset" "$@"
}

# Claude API credits from the Max plan. The key is stored under another name so
# Claude Code never picks it up; map it only inside the sandboxed pi process.
picc() {
  AGENT_HARNESS=pi _agent_sandboxed pi-local sh -c \
    'ANTHROPIC_API_KEY=$ANTHROPIC_COUNT_TOKENS_KEY exec pi "$@"' picc \
    --model anthropic/claude-sonnet-5-5:high "$@"
}

picof() {
  local session
  session="$(command picof)" || return
  pi --fork "$session" "$@"
}
