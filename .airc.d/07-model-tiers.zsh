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
        low gpt-6.1-sol:low
        mid gpt-6.1-sol:medium
        high gpt-6.1-sol:xhigh
        xhigh gpt-6.1-sol:max
        max gpt-6-astra:max
      )
      ;;
    *) return 1 ;;
  esac
  [[ -n $tier && -n ${presets[$tier]} ]] || return 1
  print -r -- "${presets[$tier]}"
}
