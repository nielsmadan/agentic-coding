# No -raw variant: pi is never run outside the sandbox.
pi() { AGENT_HARNESS=pi _agent_sandboxed pi-local pi "$@"; }

# Subscription-backed Codex model; plain `pi` keeps the OpenRouter default.
pix() { pi --model openai-codex/gpt-6-astra:medium "$@"; }

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
