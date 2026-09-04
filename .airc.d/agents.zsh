# Cross-agent helpers.

# Resume whichever agent was last active in this directory. Calls the wrapper
# functions rather than the clco/cxco/occo/pico aliases: aliases expand when the
# function is parsed, and this file is sourced before the ones defining them.
agco() {
  local agent
  agent="$(command agco)" || return
  case $agent in
    claude)   claude --continue "$@" ;;
    codex)    codex resume --last "$@" ;;
    opencode) opencode --continue "$@" ;;
    pi:openai-codex) pix --continue "$@" ;;
    pi|pi:*)  pi --continue "$@" ;;
    *)        print -u2 -r -- "agco: unknown agent '$agent'"; return 1 ;;
  esac
}
