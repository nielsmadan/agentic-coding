## Secrets

API keys live in a SOPS-encrypted file (encrypted at rest, outside this conversation's read scope). The zsh wrappers around `claude`/`codex`/`opencode`/`pi`/`nvim`/`mvim`/`neovide` run each tool through `sops exec-env`, injecting the decrypted values into **that tool's process tree only** — never the parent shell or unrelated processes.

What this means for you (the agent):

- **The injected keys ARE in your process env.** `sops exec-env` sets them on the launched tool, so the agent and every command it runs inherit them (measured 2026-09-20: `JINA_API_KEY` and `GH_TOKEN` both present in a Bash subprocess). This is deliberate — the store holds low-value dev tokens that are cheap to revoke — so treat it as normal rather than as a leak. You still have no reason to print a value, so don't echo one into the transcript. What is genuinely out of reach is the store file and the age identity.
- **Claude Code strips its own auth vars.** `CLAUDE_CODE_OAUTH_TOKEN`, `ANTHROPIC_API_KEY` and `ANTHROPIC_AUTH_TOKEN` are removed from the environment handed to tool subprocesses. That is Claude Code's own behaviour, not a decision in this setup, and it is why a nested `claude` inherits no credential — launch one through `sops-exec claude …` (with `AGENT_REQUIRE_SECRETS=1` so a failed re-injection is loud) instead of trying to read the token.
- **Don't try to decrypt, list, or print contents of the secrets store.** No `sops -d …`, no reading `~/.config/sops/age/keys.txt`, no cataloguing variable names. If an MCP call fails for lack of an env var, surface that to the user — don't try to source the value yourself.
- **Trust auto-injection for HTTP MCPs and CLI tools.** When you invoke an HTTP MCP tool, the relevant token is already in this process's env (injected at launch). You don't need to fetch or check it.
- **If a needed credential genuinely isn't injected**, ask the user. They'll decide whether to add it to the store or pass it some other way.

Architecture details (for if the user asks you to help debug or extend the setup, not for general lookup): `~/rc/CLAUDE.md` has the full description.