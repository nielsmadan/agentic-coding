# Single-shot "describe a shell command in English, get it on the prompt" helpers.
# Backed by three different LLM CLIs through pratfall, which supplies the model,
# timeout, tool restrictions and prompt template per backend — see the cmdgen-*
# profiles in ~/.config/pratfall/config.toml. Output lands on the zle buffer via
# `print -z` so the user can edit before executing — that's why this stays in zsh.
#
# sops-exec wraps prat rather than the agent: prat execs the real binary off PATH,
# bypassing the sandbox wrappers in 05-sandbox.zsh, and occli needs
# OPENROUTER_API_KEY injected. That also means these run unsandboxed, which is why
# the profiles disable tools where the backend supports it.

# Bare braille spinner; animates on stderr until killed. TTY-guarded by the caller.
_llmcli_spin() {
  local frames=(⠋ ⠙ ⠹ ⠸ ⠼ ⠴ ⠦ ⠧ ⠇ ⠏) i=1
  while true; do
    printf '\r%s' "${frames[i]}" >&2
    i=$(( i % 10 + 1 ))
    sleep 0.08
  done
}

_llmcli() {
  local profile="$1"; shift
  local input="$*"
  if [[ -z "$input" ]]; then
    local req=""
    vared -p "${profile#cmdgen-}> " req || return 0
    input="$req"
  fi
  local result spinpid
  if [[ -t 2 ]]; then
    setopt localoptions nomonitor    # background the spinner without job-control chatter
    _llmcli_spin & spinpid=$!
  fi
  result=$(printf '%s' "$input" | sops-exec prat "$profile" -t cmdgen -f - 2>/dev/null)
  if [[ -n "$spinpid" ]]; then
    kill "$spinpid" 2>/dev/null
    wait "$spinpid" 2>/dev/null
    printf '\r\033[K' >&2          # erase the spinner
  fi
  result=$(echo "$result" | sed '/^```/d;/^$/d')
  print -z "$result"
}

_ccli()  { _llmcli cmdgen-claude   "$@" }
_cxcli() { _llmcli cmdgen-codex    "$@" }
_occli() { _llmcli cmdgen-opencode "$@" }
alias ccli='noglob _ccli'
alias cxcli='noglob _cxcli'
alias occli='noglob _occli'
