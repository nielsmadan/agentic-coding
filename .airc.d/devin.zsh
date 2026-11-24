# Devin CLI. No nolabs-ai pack exists for it, so nono/devin-local.json is
# written from scratch. No -raw variant: `command devin auth login` and
# `command devin update` from your own terminal cover what the sandbox blocks.
devin() { AGENT_HARNESS=devin _agent_sandboxed devin-local devin "$@"; }

devinx() { DEVIN_MODEL=fusion-gpt-6-2-sol-max-sidekick-swe-2-high devin "$@"; }
