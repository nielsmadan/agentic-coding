# OpenCode aliases
# No -raw variant: opencode is never run outside the sandbox.
opencode() { _agent_sandboxed opencode-local opencode "$@"; }

alias oc="opencode"
alias ocs="opencode -m openrouter/meta/muse-spark-1.2"
alias occo="opencode --continue"
alias occof="opencode --continue --fork"
