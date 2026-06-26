# Single-shot "describe a shell command in English, get it on the prompt" helpers.
# Backed by four different LLM CLIs (apfli runs Apple's on-device model, fully
# offline). Output lands on the zle buffer via `print -z`
# so the user can edit before executing — that's why this stays in zsh.

_llmcli() {
  local backend="$1"; shift
  local input="$*"
  if [[ -z "$input" ]]; then
    local req=""
    vared -p "${backend}> " req || return 0
    input="$req"
  fi
  local result
  case "$backend" in
    ccli)
      result=$(claude --model haiku --tools "" --disable-slash-commands --no-session-persistence \
        --system-prompt "You are a shell command generator. Return ONLY a single shell command. No explanation, no markdown, no code blocks." \
        -p "Request: $input")
      ;;
    cxcli)
      local outfile
      outfile=$(mktemp -t cxcli.XXXXXX)
      codex exec -m gpt-5.4-mini -s read-only --skip-git-repo-check --output-last-message "$outfile" \
        "Return ONLY a single shell command that can be executed directly. No explanation, no markdown, no code blocks - just the raw command. Request: $input" >/dev/null 2>&1
      result=$(<"$outfile")
      rm -f "$outfile"
      ;;
    occli)
      result=$(opencode run -m openrouter/z-ai/glm-5 \
        "Return ONLY a single shell command that can be executed directly. No explanation, no markdown, no code blocks - just the raw command. Request: $input" | tail -1)
      ;;
    apfli)
      result=$(apfel -q --temperature 0 \
        -s "You are a shell command generator. Return ONLY a single shell command. No explanation, no markdown, no code blocks." \
        -- "$input")
      ;;
    *)
      echo "_llmcli: unknown backend '$backend'" >&2
      return 2
      ;;
  esac
  result=$(echo "$result" | sed '/^```/d;/^$/d')
  print -z "$result"
}

_ccli()  { _llmcli ccli  "$@" }
_cxcli() { _llmcli cxcli "$@" }
_occli() { _llmcli occli "$@" }
_apfli() { _llmcli apfli "$@" }
alias ccli='noglob _ccli'
alias cxcli='noglob _cxcli'
alias occli='noglob _occli'
alias apfli='noglob _apfli'
