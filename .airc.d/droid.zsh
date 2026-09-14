# Factory droid. No nolabs-ai pack exists for it, so nono/droid-local.json is
# written from scratch rather than extending one.
#
# No -raw variant: droid is never run outside the sandbox. Its interactive login
# stores the session through keytar — the macOS login keychain, denied on
# purpose — so runs authenticate with FACTORY_API_KEY from the sops store, which
# droid prefers over a stored login anyway. Droid also carries its own
# rule-based autonomy layer, so nono is the outer boundary rather than the only
# one.
droid() { AGENT_HARNESS=droid _agent_sandboxed droid-local droid "$@"; }
