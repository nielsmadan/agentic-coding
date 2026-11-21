# House settings

What every agent on this machine gets, with the value each harness carries today.
Read the live files before copying a value: they change, this table does not
update itself. "—" means nothing is set in this repo, not that the harness lacks
the feature.

## Permission mode

The rule: a **model-reviewed** mode, where a classifier or fast model approves
routine actions and asks about the rest. Fall back to full bypass only when the
harness has no reviewed mode, or when the user asks for it. nono is the boundary
either way, and loadout's deny rules (`git push`) still apply in bypass.

| Harness | Setting | Where |
|---|---|---|
| Claude | `permissions.defaultMode: "auto"`, `skipAutoPermissionPrompt: true` | `loadout/settings/claude.json` |
| Codex | `approval_policy: "on-request"`, `approvals_reviewer: "auto_review"` | `loadout/defaults/codex.json` |
| Droid | `sessionDefaultSettings.autonomyLevel: "high"` | `loadout/settings/droid.json` |
| Devin | `permission_mode: "dangerous"` (the user's choice on 2026-11-21; `smart` is its reviewed mode) | `loadout/settings/devin.json` |
| Cursor | `approvalMode: "unrestricted"` | `~/.cursor/cli-config.json`, not loadout-owned |
| OpenCode, Pi | — | |

An `Exec(*)`-style catch-all allow is not a substitute: in Devin it covered
`touch x` but still prompted for `a && b` and for a heredoc written outside the
workspace.

## Status line

One layout everywhere, from `loadout/module-config/claude/hooks/statusline.sh`
and Pi's `loadout/module-config/pi/extensions/statusline/index.ts`:

- `🔒` green when `AGENT_SANDBOX` or `NONO_CAP_FILE` is set, `🥩` red otherwise (priority 100, never dropped)
- `🤖 model effort`: lowercase, `claude-` prefix stripped, spaces removed, yellow model and magenta effort (priority 60)
- `🧠` 10-cell `▓░` context bar plus percent, colour steps at 45/70/90% (priority 80)
- quota windows when the harness exposes them (`⏳`, priority 70)
- segments joined by a dim ` │ `, lowest priority dropped first when the width runs out

| Harness | How |
|---|---|
| Claude | command `~/.claude/hooks/statusline.sh`, `refreshInterval: 60` |
| Codex | built-in items: `project-name`, `model-with-reasoning`, `context-used`, `weekly-limit`, `thread-name` |
| Droid | command `~/.factory/statusline.sh` (→ `statusline.py`, fetches Factory limits) |
| Pi | `statusline` extension |
| Devin | none: the CLI has no custom status line (3000.14) |
| Cursor, OpenCode | — |

## Everything else

| Concern | House value | Examples |
|---|---|---|
| Default model | the session-tier pick for that harness's provider, at the tier's effort | `agent-models` skill; `devin.json` `agent.model` |
| Session history | keep forever | Claude `cleanupPeriodDays: 9999`; Droid logs kept (commit aa2af47) |
| Commit attribution | none | Claude `attribution` empty; Droid `includeCoAuthoredByDroid: false`; Devin `attribution: false` |
| Quiet UI | sounds, animations, hints, whimsy and recaps off; dark theme | Droid sounds/logo off; Codex `whimsy`/`auto_recap` false; Claude `awaySummaryEnabled: false`; Devin `show_hints: false` |
| Updates | no startup check or background install; updated by `bin/update-agents` from the user's terminal | Codex `check_for_update_on_startup: false`; Devin `auto_update: false` |
| Subagents | 16 concurrent, depth 2 | Claude env vars; Codex `max_concurrent_threads_per_session`; OpenCode `subagent_depth` |
| Harness's own sandbox | off: nono blocks a nested Seatbelt profile | Cursor `sandbox.mode: "disabled"`; Devin without `--sandbox` |
| Imports of other harnesses' config | off, since loadout renders each harness its own copy | Devin `read_config_from.*: false` (except `agents_standard` and `cloud`) |
| Sandbox status note | a `SessionStart` hook running `agent-sandbox-status`, in the format the harness reads | `loadout/hooks/<agent>.json`; plain stdout for Claude and Codex, JSON for Cursor and Devin |
| Juggler | hooklinesinker hooks with `~/`-relative commands | `loadout/juggler/hooks/hooklinesinker-<agent>.json` |
| Credentials | an API key from the sops store; keychain logins fail in nono | Cursor `CURSOR_API_KEY` + `AGENT_CLI_CREDENTIAL_STORE=memory`; Droid `FACTORY_API_KEY` |
| Instructions, skills, MCP, shell rules | rendered by loadout once the harness has a table in `loadout.toml` | `[all]` instructions; `loadout/permissions.toml` |

## Files a new harness touched

Devin (1b1d519, fdb2cb9, 5bfae48) and Cursor (09dc19b, bfb3608, 7fd7e24, bd1f62a,
57e0d38, b000d6d):

- `nono/<agent>-local.json`, `nono/writable-baseline.txt`, `sync.sh` symlink, `docs/nono-grants.md`
- `.airc.d/<agent>.zsh`, `.airc.d/05-sandbox.zsh` (`--silent` list)
- `bin/update-agents` and `bin/test_update_agents.py`
- `loadout.toml`, `loadout/settings/<agent>.json` (+ generated `.owned`), `loadout/hooks/<agent>.json`
- `loadout/juggler/hooks/hooklinesinker-<agent>.json` (and `studio-agents.toml` if the fleet runs it)
- `bin/agent-sandbox-status` and its test, when the hook needs a different output format
- `loadout/skills/check-agent-logs/scripts/search_agent_logs.py` and its test; `skill-usage` tests; `bin/term-peek` `AGENTS`
- `AGENTS.md` structure and sandbox sections
