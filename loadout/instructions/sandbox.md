## Sandbox

Agent CLIs run either inside a [nono](https://github.com/nolabs-ai/nono) Seatbelt sandbox or
raw: `claude` and `codex` launch raw inside `~/ac` and `~/rc`, and `claude-raw` / `codex-raw`
anywhere. **A "Sandbox status" note at session start says which one this session is** — go by
it, not by assumption. Without it, `nono why --self` prints `NOT SANDBOXED` outside the sandbox.
Instructions that distinguish a sandboxed from an unsandboxed session mean exactly this.

Inside the sandbox, `~/wrksp` is read+write; most of the rest of `$HOME` is not. The rest of this
section is about sandboxed sessions; a raw session has none of these limits.

**On `Operation not permitted`, EPERM, EACCES, `sandbox-exec: sandbox_apply` or a nono denial
footer, load the `nono-sandbox` skill before concluding anything.** Most such failures here are
not missing grants — a tool starting its own sandbox, a harmless probe next to an unrelated
failure, a misread diagnostic. Check with `nono why --self --path <path> --op <op>`; a bare
`nono why` is never evidence. **Never offer a grant as the first remedy**: verify, then report,
and leave the grant to the user. Never work around a real denial by relocating files or
weakening a test.

**Some paths are denied on purpose and stay denied** — `~/Library/Keychains/login.keychain-db`,
`~/.ssh`, and `~/.local/state/mise/trusted-configs` among them. Do not propose a grant for these:
name the blocker, hand the user the command to run in their own terminal (a `!` command runs
inside the same sandbox and hits the same denial), and carry on with the rest.

**`uvx` needs its directories redirected, not granted:**
`env UV_TOOL_DIR="$WORKDIR/.uv/tools" UV_CACHE_DIR="$WORKDIR/.uv/cache" uvx --from <pkg> <cmd>`.
