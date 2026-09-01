# Single-shot "describe a shell command in English, get it on the prompt" helpers.
# Backed by three different LLM CLIs. Output lands on the zle buffer via `print -z`
# so the user can edit before executing — that's why this stays in zsh.

# Bare braille spinner; animates on stderr until killed. TTY-guarded by the caller.
_llmcli_spin() {
  local frames=(⠋ ⠙ ⠹ ⠸ ⠼ ⠴ ⠦ ⠧ ⠇ ⠏) i=1
  while true; do
    printf '\r%s' "${frames[i]}" >&2
    i=$(( i % 10 + 1 ))
    sleep 0.08
  done
}

# Run one backend, emitting the generated command to stdout.
_llmcli_run() {
  local backend="$1" input="$2"
  case "$backend" in
    ccli)
      claude --model haiku --tools "" --disable-slash-commands --no-session-persistence \
        --system-prompt "You are a shell command generator. Return ONLY a single shell command. No explanation, no markdown, no code blocks." \
        -p "Request: $input"
      ;;
    cxcli)
      local outfile
      outfile=$(mktemp -t cxcli.XXXXXX)
      codex exec -m gpt-5.4-mini -s read-only --skip-git-repo-check --output-last-message "$outfile" \
        "Return ONLY a single shell command that can be executed directly. No explanation, no markdown, no code blocks - just the raw command. Request: $input" >/dev/null 2>&1
      cat "$outfile"
      rm -f "$outfile"
      ;;
    occli)
      opencode run -m openrouter/openai/gpt-5.6-luna \
        "Return ONLY a single shell command that can be executed directly. No explanation, no markdown, no code blocks - just the raw command. Request: $input" | tail -1
      ;;
    *)
      echo "_llmcli: unknown backend '$backend'" >&2
      return 2
      ;;
  esac
}

_llmcli() {
  local backend="$1"; shift
  local input="$*"
  if [[ -z "$input" ]]; then
    local req=""
    vared -p "${backend}> " req || return 0
    input="$req"
  fi
  local result spinpid
  if [[ -t 2 ]]; then
    setopt localoptions nomonitor    # background the spinner without job-control chatter
    _llmcli_spin & spinpid=$!
  fi
  result=$(_llmcli_run "$backend" "$input" 2>/dev/null)
  if [[ -n "$spinpid" ]]; then
    kill "$spinpid" 2>/dev/null
    wait "$spinpid" 2>/dev/null
    printf '\r\033[K' >&2          # erase the spinner
  fi
  result=$(echo "$result" | sed '/^```/d;/^$/d')
  print -z "$result"
}

_ccli()  { _llmcli ccli  "$@" }
_cxcli() { _llmcli cxcli "$@" }
_occli() { _llmcli occli "$@" }
alias ccli='noglob _ccli'
alias cxcli='noglob _cxcli'
alias occli='noglob _occli'
