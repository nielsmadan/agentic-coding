## React Native project tooling

This project ships with a React Native-aware Claude setup deployed by `aiconf react-native` —
device-control MCP servers and a project-scoped upgrade skill. Use them where they help.

### When to reach for the deployed MCPs

- **`ios-sim`** — driving the booted iOS simulator: screenshots, view tree dumps, taps,
  swipes, text input, point-to-element introspection. Use it for UI smoke checks and
  reproducing visual issues after a code change. Works for any iOS app — RN's bridge to
  native is invisible to it.
- **`android`** — analogous control over Android devices/emulators when working on the
  Android target.

There is no JavaScript/TypeScript MCP server bundled. For static analysis and tests use the
project's own scripts directly (`yarn type-check`, `yarn lint`, `yarn test`); for library
docs use `/research-code`.

### Streaming Metro logs (`rn-logs`)

Use [`rn-logs`](https://github.com/okwasniewski/react-native-logs-cli) (npm package
`rn-logs-cli`) to read the JavaScript runtime logs Metro collects via CDP — `console.log`/
`warn`/`error`, redbox content, Hermes uncaught exceptions, anything your JS surfaces while
the app is running. It's purpose-built for agent consumption (plain-text output, low
context). Pre-approved in `.claude/settings.local.json`.

```bash
rn-logs apps                                  # list apps connected to Metro
rn-logs logs --app <name>                     # follow logs for that app
rn-logs logs --app <name> --limit 50          # snapshot last 50 lines then exit
rn-logs logs --app <name> --verbose           # include full stack traces
```

Notes:
- Metro defaults to `localhost:8081`. If this project runs Metro on a different port (check
  `package.json` `scripts.start`), pass `--port <n>` to both `apps` and `logs`.
- `rn-logs` attaches to Metro's CDP inspector channel. **It cannot run simultaneously with
  React Native DevTools** — they compete for the channel. Pick one per session.
- Use this for JS-side issues. For native crashes / NSLog output / adb logcat, use
  `npx react-native log-ios` or `log-android` directly (not pre-approved; will prompt).

### When to reach for the deployed skill

- **`/rn-upgrade`** — bumping the React Native SDK or doing a major version migration
  (e.g., 0.83 → 0.84). It fetches the upgrade diff, identifies breaking changes, and walks
  through native-side adjustments. Don't invoke it for routine dependency bumps
  (`yarn upgrade-interactive` covers minor JS deps).

### Notes

- These MCPs and the skill arrive via `aiconf react-native`. Re-running it refreshes their
  config but leaves this CLAUDE.md section alone — use `aiconf sync` to mirror edits back to
  the template or pull template changes into this section.
- Only the `ios-sim` tools are pre-approved in `.claude/settings.local.json`. The first call
  to an `android` tool will trigger a permission prompt — approve there, and add the specific
  tool name to `permissions.allow` if you want it auto-approved going forward.
- Machine prerequisites: `npx` and `uvx` for the MCP servers; `rn-logs-cli` installed
  globally for log streaming (`npm install -g rn-logs-cli` or `bun add -g rn-logs-cli`).
