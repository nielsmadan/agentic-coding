# No -raw variant: pi is never run outside the sandbox.
pi() { AGENT_HARNESS=pi _agent_sandboxed pi-local pi "$@"; }

# Subscription-backed Codex model; plain `pi` keeps the OpenRouter default.
pix() { pi --model openai-codex/gpt-5.6-sol:max "$@"; }

alias pico="pi --continue"
alias pixco="pix --continue"

picof() {
  local session
  session="$(command picof)" || return
  pi --fork "$session" "$@"
}
