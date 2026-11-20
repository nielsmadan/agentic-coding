_agent_model_tier() {
  local provider=$1 tier=$2
  local -A presets
  case $provider in
    anthropic)
      presets=(
        low claude-haiku-5-5:xhigh
        mid claude-sonnet-5-5:high
        high claude-opus-5-5:high
        xhigh claude-fable-5-2:medium
        max claude-fable-5-2:max
      )
      ;;
    openai)
      presets=(
        low gpt-6.2-sol:low
        mid gpt-6.2-sol:medium
        high gpt-6.2-sol:max
        xhigh gpt-6.2-astra:high
        max gpt-6.2-astra:max
      )
      ;;
    *) return 1 ;;
  esac
  [[ -n $tier && -n ${presets[$tier]} ]] || return 1
  print -r -- "${presets[$tier]}"
}
