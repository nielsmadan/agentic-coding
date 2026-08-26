# Security model

How agents on this machine are contained, what that containment does and does not
cover, and why `git push` behaves differently in each context.

## What we are guarding against

The goal is **guardrails with no friction during use or maintenance**, not an
ironclad boundary. Concretely: an agent should not be able to wreck the machine
or quietly acquire control of it. Everything under `~/wrksp` is backed up and
recoverable, so losing work there is an annoyance rather than a disaster.

That framing decides most of what follows. Where a control costs nothing it is
kept; where it costs friction and duplicates something already enforced, it is
dropped.

### What nono covers

[nono](https://github.com/nolabs-ai/nono) is a Seatbelt-based capability sandbox.
It mediates **filesystem access**: an agent can read and write only the paths its
profile grants. That is what stops an agent from rewriting shell config, planting
a binary on `PATH`, reading credentials it was not given, or deleting things
outside its workspace.

### What nono does not cover

| Not covered | Consequence |
|---|---|
| **Network** | Outbound is wide open. Exfiltration of anything readable is not addressed at all. |
| **Destruction inside granted paths** | `rm -rf ~/wrksp/<project>` is fully permitted. `~/wrksp` is the largest grant and the real work lives there. |
| **Remote side effects** | Pushes, deploys, cloud deletes, API spend — the sandbox cannot see them. |

The first two are accepted. The third is handled by credentials rather than by
the sandbox: see below.

## Where each agent runs

| Agent | Sandboxed | Raw variant | Notes |
|---|---|---|---|
| `claude` | yes | `claude-raw` | auto-routes to raw inside `~/ac` and `~/rc` |
| `codex` | yes | `codex-raw` | same auto-routing |
| `opencode` | yes | **none** | never runs outside the sandbox |
| `pi` | yes | **none** | never runs outside the sandbox |

The auto-routing exists because work in `~/ac` and `~/rc` writes outside
`~/wrksp` by definition. `AGENT_FORCE_SANDBOX=1` overrides it.

Because `opencode` and `pi` are sandbox-only, nono is *always* their boundary.
That is why their approval layers were removed — a prompt there adds friction
without adding containment. Adding a `pi-raw` or `opencode-raw` would invalidate
that reasoning and needs this document revisited.

## Git and GitHub authentication

**`gh`** uses read-only fine-grained PATs injected from the sops store. There is
no write-capable GitHub credential on this machine: `~/.config/gh/hosts.yml`
holds nothing, and the keyring login was removed. Verified — with the token
unset, `gh auth status` reports *"You are not logged into any GitHub hosts."*

Fine-grained PATs are scoped to a single resource owner, so one token cannot
cover both a personal account and an organisation. `bin/gh` picks
`GH_TOKEN_<OWNER>` from the repo owner and execs the real `gh`, falling back to
`GH_TOKEN`.

**`git`** authenticates over ssh, using the keys in `~/.ssh` and the ssh-agent.
Pushes are forced onto ssh even for https remotes:

```gitconfig
[url "git@github.com:"]
	pushInsteadOf = https://github.com/     # ~/rc/.gitconfig
[url "git@gitlab.com:"]
	pushInsteadOf = https://gitlab.com/     # ~/.gitconfig-efg, EFG repos only
```

`pushInsteadOf`, not `insteadOf` — fetches stay on https so they keep working
with the read-only token, while pushes take the ssh path.

## How `git push` is stopped

Three contexts, three different answers.

### Sandboxed agent — blocked three times over

1. **`~/.ssh` is denied** by the sandbox — key *and* config. ssh cannot
   authenticate, so the `pushInsteadOf` path dead-ends.
2. **The token is read-only**, so an https push returns
   `403 Resource not accessible by personal access token`.
3. **The harness denies it** (see the table below).

Any one of these suffices. This is the well-defended case.

### Raw agent (`claude-raw`, `codex-raw`) — one layer only

There is no sandbox, so `~/.ssh` and the ssh-agent are both reachable and a push
would succeed on credentials alone. **The harness deny rule is the only thing
stopping it:**

| Harness | Rule | Rendered as |
|---|---|---|
| Claude | `deny` beats every mode, including `auto` | `Bash(git push:*)` |
| Codex | `prefix_rule(pattern = ["git", "push"], decision = "forbidden")` | `~/.codex/rules/permissions.rules` |
| OpenCode | `git push` / `git push *` → `deny` | sandbox-only, so raw does not apply |
| Pi | **none** | permission module removed; sandbox-only |

A deny list is a speed bump, not a boundary: the matched string is chosen by the
caller, so `git -C /repo push`, `env X=1 git push`, or a one-line script all miss
the pattern. Treat raw sessions as supervised, which is what they are for.

### Interactive shell — deliberately unrestricted

Nothing stops you. Your shell has the ssh keys and agent, `pushInsteadOf` routes
pushes to ssh, and none of the agent permission config applies to you. The only
thing this repo adds to your shell is a `gh()` function that routes to
`bin/gh`.

> Note: `gh` in your own terminal is **unauthenticated**, because the sops
> injection wraps the agent CLIs and editors, not `gh`. Use `_sops_exec gh …`
> for a one-off, or add a wrapper next to the editor ones in `~/rc/.zshrc`.

## The approval layer, and why it is thin

The shared shell allowlist was retired. An `allow` entry can only *suppress a
prompt* — it never bounded anything — so 202 entries of it were maintenance cost
with no security value. What remains is:

- `[shell] default = "allow"` — the catch-all, authored for **OpenCode and Pi
  only**. Claude's catch-all is `permissions.defaultMode` (still `auto`) and
  Codex's is `approval_policy`; loadout writes neither, so neither was loosened.
- `[shell] deny = ["git push"]` — the single restriction, kept because it is the
  one capability with no backstop in a raw session.

`default = "allow"` makes the deny list subtractive, which is weaker than it
looks: spellings that miss the pattern now execute silently instead of
prompting. Accepted because it applies only to the two always-sandboxed
harnesses, where a push fails on credentials regardless.

## Known gaps

Recorded so they are decisions rather than oversights.

- **Network is open everywhere.** Anything an agent can read, it can send.
- **Any agent can write any other agent's config.** All four profiles hold
  read+write on `~/.claude`, `~/.codex`, `~/.pi` and `~/.config/opencode`, so one
  agent can edit another's instructions. Transient — the next `loadout sync`
  regenerates them — but real between syncs.
- **Session transcripts are deletable** by the agent that owns them, and now by
  any agent, since those directories are mutually writable.
- **Pi has no approval layer at all.** Its core ships none and the extension was
  removed. Entirely dependent on being sandbox-only.
- **`mise trust` is deliberately withheld** (`~/.local/state/mise/trusted-configs`
  is not granted). A trusted `mise.toml` applies its `[env]` — including
  `_.path` — to your interactive shell in that directory, which would be a route
  out of the sandbox. Run `mise trust` yourself when a repo needs it.

## See also

- [`AGENTS.md`](../AGENTS.md) — sandbox profiles, grants, per-agent quirks, and
  the gotchas catalogue.
- `loadout/permissions.toml` — the permission source.
- `nono/*.json` — the sandbox profiles; `bin/nono-audit` guards the writable set.
