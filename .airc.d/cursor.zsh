# Cursor CLI. No nolabs-ai pack exists for it, so nono/cursor-local.json is
# written from scratch. The installer links both `cursor-agent` and `agent`, so
# both are wrapped; an unwrapped `agent` would run outside the sandbox.
#
# No -raw variant. Its interactive login lives in the macOS login keychain,
# denied on purpose, so runs authenticate with CURSOR_API_KEY from the sops
# store, and the profile sets AGENT_CLI_CREDENTIAL_STORE=memory so nothing is
# persisted to the keychain or to ~/.cursor/auth.json.
cursor-agent() { AGENT_HARNESS=cursor _agent_sandboxed cursor-local cursor-agent "$@"; }
agent() { AGENT_HARNESS=cursor _agent_sandboxed cursor-local cursor-agent "$@"; }
