# Global CLAUDE.md

User-scoped guidance that applies to every Claude Code session on this machine. Loaded from `~/.claude/CLAUDE.md` (symlinked to this file).

Keep this file **project-agnostic** — anything specific to a particular repo belongs in that repo's own `CLAUDE.md`.

## Web Fetching

External URLs are best fetched through the Jina MCP server, which renders JS server-side and returns clean markdown — avoiding the HTML-skeleton problem `WebFetch` has on SPAs.

**Default**: use `mcp__jina__read_url` (or `mcp__jina__parallel_read_url` for multiple URLs) for external pages.

**Use plain `WebFetch` for**:
- `github.com` URLs (repo pages, issues, PRs, raw files) — already return sensible HTML
- Local dev servers (`localhost`, `127.0.0.1`)
- Plain HTML/RSS/Atom/PDF where the Jina detour adds latency without value

**Fall back to `WebFetch`** if the Jina MCP is unavailable (key missing, rate-limited, server down) or returns thin content.

**Authenticated or anti-bot sites** are not supported via either path — use `gh`, `glab`, or project-specific CLIs instead.

**Auth**: the Jina MCP's auth happens automatically — token comes from the SOPS-encrypted store via the `claude` zsh wrapper, interpolated into the request header by Claude Code at startup. The agent does not need to know or fetch the value (see Secrets below).

## Secrets

API keys are deliberately kept **out of Claude Code's reach**. They live in a SOPS-encrypted file outside this conversation's read scope, and the zsh wrappers around `claude`/`codex`/`agy`/`opencode`/`nvim`/`mvim`/`neovide` inject only the values needed into each subprocess. The point of this setup is that the model cannot enumerate, read, or echo secrets — not that the model needs convenience access to them.

What this means for you (the agent):

- **Don't look for API keys in shell env.** They aren't there. `env | grep -i key`, sourcing `~/.airc`, reading `~/.zshrc`, etc. won't find them.
- **Don't try to decrypt, list, or print contents of the secrets store.** No `sops -d …`, no reading `~/.config/sops/age/keys.txt`, no cataloguing variable names. If an MCP call fails for lack of an env var, surface that to the user — don't try to source the value yourself.
- **Trust auto-injection for HTTP MCPs and CLI tools.** When you invoke an MCP like `mcp__jina__read_url`, the relevant token is already in this process's env (injected at launch). You don't need to fetch or check it.
- **If a needed credential genuinely isn't injected**, ask the user. They'll decide whether to add it to the store or pass it some other way.

Architecture details (for if the user asks you to help debug or extend the setup, not for general lookup): `~/rc/CLAUDE.md` has the full description.

## Git Policy

Leave git to the user. Do not run git commands that modify state (`add`, `commit`, `checkout`, `branch`, `merge`, `rebase`, `stash`, etc.) unless the user explicitly asks for that specific operation. A few commands are hard-blocked at the harness level — `git push`, `git branch -d/-D`, `git reset --hard`, `git clean -f*` — because they push to a remote or destroy local work; ask the user to run those manually.

Read-only inspection (`status`, `log`, `diff`, `show`, `branch` listing, etc.) is always fine.

### Commit Granularity

When the user asks you to commit, aim for a clean final history rather than maximum granularity:

- **Small checkpoint commits while working are fine** — they're useful for recovery and incremental review.
- **Multiple commits are fine** when each represents a logical, self-contained change (e.g. "refactor X" + "add feature Y on top").
- **Avoid leaving "half a feature" in history.** A commit that only makes sense in conjunction with the next one (WIP, "part 1 of N", broken intermediate state) is a checkpoint, not a history entry.
- **Look back as soon as a sub-feature is done** — don't wait for the whole task to wrap up. The moment a sub-feature is complete, combine its initial development, the fixes that went on top, its tests, and its docs into one commit. Workflows that emit many small commits (e.g. superhuman, gsd) make this especially important; most of those commits are checkpoints, not history entries.
- When a task wraps up, proactively suggest squashing checkpoint commits into the smallest set that each stand on their own. Don't rewrite history without explicit approval — propose the squash plan and let the user confirm. The `squash-commits` skill automates this over the unpushed range.

### Commit Message Format

Use only these three types — no others, no scopes:

- **`feat`** — something was added that is noticeable by the user
- **`fix`** — something was not working correctly and was fixed
- **`chore`** — everything else (refactoring, fixing tests, internal changes, etc.)

Do **not** use parentheses/scopes: write `feat: add login button`, not `feat(ui): add login button`.

**Body**: keep it short or omit it entirely. The body identifies *what* was done, not *why* or *how*. No essays, no implications, no test counts, no rationale. Max 4 sentences — and don't pad to reach 4. One sentence or no body at all is usually right.
