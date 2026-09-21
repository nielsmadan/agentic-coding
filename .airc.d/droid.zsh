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

alias drco="droid resume --last"

# Keep the router-decision logs in ~/.factory/logs indefinitely. Droid prunes on
# whichever of these binds first and has no unlimited sentinel, so the caps are
# set past any reachable value instead; the defaults (30 days, 1 GiB) drop about
# ten days at ~90 MB/day.
export FACTORY_LOG_MAX_DAYS=1000000
export FACTORY_LOG_MAX_TOTAL_BYTES=9007199254740991
