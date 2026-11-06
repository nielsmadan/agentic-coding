## Machine

This is the Mac Studio that runs the agent fleet. Agent CLIs run here without nono: each
agent's own approval settings still apply, and the machine itself is the boundary. Diagnose
failures from the active session's permissions and the tool's error output.

Niels's own sessions and every agent run as the same non-admin user. There is no `sudo`, and
Homebrew belongs to the `admin` account, so `brew install` fails by design.

**Do not install software yourself.** No global installs (`npm -g`, `uv tool install`,
`cargo install`, `pipx`, `go install`, `mise install`, `mise use -g`, binaries dropped into
`~/.local/bin`) and no
run-without-install (`npx`, `uvx`, `bunx`, `pnpm dlx`, `yarn dlx`, `npm exec`). A tool is either
part of the project, run through its package scripts or `uv run`, or installed through the
package gate: report the package and why it is needed, and Niels installs it as admin.

**`agent-browser` is here for testing web apps.** It launches its own Chrome, logged into
nothing. Give every task its own `--session <name>` and close it when done, so parallel sessions
never drive each other's pages. Never point it at another browser or profile (`--cdp`,
`--auto-connect`, `--profile`). If it reports a missing browser, report that rather than running
`agent-browser install`.

**Other sessions share this machine.** Work only in worktrees you created or were given. Never
`git clean`, `git reset --hard`, stash or delete in another session's worktree, and never kill
what you did not start: no `pkill node`, no `adb kill-server`, no shutting down a simulator or
emulator another session may be using.
