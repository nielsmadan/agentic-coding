## Mobile project tooling

### Driving the app (`agent-device`)

Use [`agent-device`](https://github.com/callstack/agent-device) (Callstack's device-automation
CLI, installed globally, on `PATH`) to drive the running app on an iOS simulator, Android
emulator, or physical device — verify a UI change, reproduce a click-path, or grab a screenshot.
It reads the app's accessibility tree and exposes `@e` refs for interaction across native,
React Native, Expo, and Flutter apps. Good accessibility labels and test IDs make runs more
reliable.

**Start here**: run `agent-device help workflow` once per session for the command reference and
workflow patterns — the installed CLI help is the source of truth. Run `agent-device doctor`
to verify local setup. Prefer that over guessing flags.

**Core loop** (commands in one session run serially; the session persists until `close`):

- `agent-device apps --platform ios|android` — list installed apps.
- `agent-device open <App> --platform ios|android` — start a session using a discovered app.
- `agent-device snapshot -i` — read interactive elements with refs like `@e1`, `@e2`.
- `agent-device press @e2 --settle` / `agent-device fill @e3 "<text>" --settle` — interact
  using current refs and inspect the settled diff.
- `agent-device screenshot <path>` — save a PNG, then read it to see the screen.
- `agent-device close` — end the session.

Refs expire when app state changes. Use refs from the latest snapshot or settled diff; take a
fresh `snapshot -i` when the diff lacks the next target or the UI has not settled. See
`agent-device help workflow` for typing, scrolling, gestures, waits, assertions, and alerts.

### Setup

The `mobile`, `flutter`, and `react-native` templates select this shared guidance and the
`agent-device` shell permission for the project's configured harnesses. Run `loadout sync` in
the project after changing its templates.

Install `agent-device` globally (`npm install -g agent-device`), with Xcode for iOS and the
Android SDK + ADB for Android. Template sync supplies configuration; install these machine
prerequisites separately.
