## Secrets

This machine has its own SOPS-encrypted store, holding only tokens scoped to the Studio and
cheap to revoke. The launchers run each agent through `sops-exec`, which injects the decrypted
values into that tool's process tree only.

- **The injected keys are in your process env**, and every command you run inherits them. That
  is deliberate. You have no reason to print a value, so never echo one into a transcript, log,
  commit or message.
- **Nothing on this machine stops you reading credential files; don't.** No `sops -d …`, no
  reading the age identity, no cataloguing variable names, and no reading other tools'
  credentials (`gh`'s hosts file, Codex's `auth.json`, Claude's credentials, the keychain,
  the commit signing key in `~/fleet/keys`).
- **Never use `SSH_AUTH_SOCK` or a forwarded SSH agent, even when one is present.** It belongs to
  Niels and asks him for Touch ID on each use. Git and `gh` both act as the factory's dev
  account, over HTTPS with its scoped token(s). Never run `gh auth login`,
  `ssh-keygen` or `ssh-add`, and never write a token to a file, the keychain or a git credential
  store. If a push or a pull request fails for lack of a credential, report it.
- **Claude Code strips its own auth vars.** `CLAUDE_CODE_OAUTH_TOKEN`, `ANTHROPIC_API_KEY` and
  `ANTHROPIC_AUTH_TOKEN` are removed from the environment handed to tool subprocesses, so a nested
  `claude` inherits no credential — launch one through `sops-exec claude …` (with
  `AGENT_REQUIRE_SECRETS=1` so a failed re-injection is loud).
- **If a needed credential isn't injected, report it**, naming the variable and what needed it.
  Don't try to source the value yourself.
