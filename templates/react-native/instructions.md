## React Native project tooling

This project ships with a React Native-aware Claude setup deployed by `aiconf react-native` —
a device-automation CLI and a project-scoped upgrade skill. Use them where they help.

### Driving the app (`agent-device`)

Use [`agent-device`](https://github.com/callstack/agent-device) (Callstack's device-automation
CLI, installed globally, on `PATH`) to drive the running app — booted iOS simulator, Android
emulator, or a physical device — to verify a UI change, reproduce a click-path, or grab a
screenshot. It's the device counterpart to `agent-browser`: text-first output, low token cost,
and a token-efficient accessibility snapshot with stable `@e` refs instead of brittle
coordinates. One CLI covers both platforms (iOS via XCTest, Android via ADB).

**Start here**: run `agent-device help workflow` once per session for the full command
reference and workflow patterns — the installed CLI help is the source of truth. Run
`agent-device doctor` to verify local setup. Prefer that over guessing flags.

**Core loop** (the session is stateful and persists across invocations until `close`, so each
command below is its own shell call against the same live session):
- `agent-device apps --platform ios|android` — list installed apps.
- `agent-device open <App> --platform ios|android` — start a session.
- `agent-device snapshot -i` — accessibility tree, interactive elements only, with refs like
  `@e1`, `@e2`. Use those refs to target elements.
- `agent-device tap @e2` / `fill @e3 "<text>"` — interact using those refs. See
  `agent-device help workflow` for the full command set (typing, swipe, scroll, gestures,
  wait, assert, alerts, …).
- `agent-device screenshot <path>` — save a PNG (then read it to see the screen).
- `agent-device close` — end the session.

Refs are only valid for the **latest** snapshot — after scrolling or changing screens, take a
fresh `snapshot`. Snapshots come from the app's accessibility tree, so it works for any app
(native, RN, Expo, Flutter) and RN's JS↔native bridge is invisible to it — good accessibility
labels and test IDs make runs far more reliable. Reach for this whenever you need to see or
interact with the actual app; for JS-side runtime logs use `rn-logs` (below).

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

- This tooling and the skill arrive via `aiconf react-native`. Re-running it refreshes their
  config but leaves this CLAUDE.md section alone — use `aiconf sync` to mirror edits back to
  the template or pull template changes into this section.
- `agent-device` and `rn-logs` are pre-approved in `.claude/settings.local.json`
  (`Bash(agent-device:*)`, `Bash(rn-logs:*)`), so their subcommands run without a prompt.
- Machine prerequisites: `agent-device` installed globally (`npm install -g agent-device`,
  Node.js 22+; plus Xcode for iOS and the Android SDK + ADB for Android); `rn-logs-cli`
  installed globally for log streaming (`npm install -g rn-logs-cli` or `bun add -g rn-logs-cli`).
