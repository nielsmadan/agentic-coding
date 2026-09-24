## React Native project tooling

Use `templates = ["react-native"]` in `loadout/config.toml`. This template includes shared
mobile device automation, Metro log tooling, and a project-scoped upgrade skill. For JavaScript
runtime logs use `rn-logs` below.

For static analysis and tests use the project's own scripts directly (`yarn type-check`,
`yarn lint`, `yarn test`); for library docs use `/research-tech`.

### Metro ports (`splashdown`)

Let Splashdown assign and manage Metro's port. Do not choose a port, hardcode `8081`, or
start a separate packager with an agent-selected port. When a command needs this checkout's
assigned port, read `RCT_METRO_PORT` from `splashdown.env` and use that value for Metro,
device launches, reloads, and log tooling.

Check whether `splash run` starts Metro in the installed version (`docs/user/devices.md` in
splashdown). If it does not, start Metro yourself on the assigned port, in the background with
its output in a log file, before `splash run`. When calling `run-ios` / `run-android` directly,
pass `--no-packager`: otherwise the CLI opens its own packager through LaunchServices, which
fails inside the sandbox with `_LSOpenURLsWithCompletionHandler() failed with error -54`. On
Android, `adb reverse tcp:$RCT_METRO_PORT tcp:$RCT_METRO_PORT` after every connect, plus any
backend port the app calls.

### Build once, then reload

A native build, re-sign and reinstall takes minutes; a Metro reload takes seconds. When only
JavaScript changed and a build of this checkout is already installed, reload through Metro
(`agent-device metro reload --metro-port $RCT_METRO_PORT`, which otherwise falls back to 8081,
or relaunch the app) instead of rebuilding. Rebuild when native
code, native dependencies, `ios/` / `android/`, or values compiled into the build
(react-native-config `.env` values) changed.

Run CocoaPods through the project's Gemfile, `cd ios && bundle exec pod install`, never a global
`pod`. A version mismatch between the two rewrites `Podfile.lock` and churns
`project.pbxproj`.

### Streaming Metro logs (`rn-logs`)

Use [`rn-logs`](https://github.com/okwasniewski/react-native-logs-cli) (npm package
`rn-logs-cli`) to read the JavaScript runtime logs Metro collects via CDP — `console.log`/
`warn`/`error`, redbox content, Hermes uncaught exceptions, anything your JS surfaces while
the app is running. It's purpose-built for agent consumption (plain-text output, low
context). The React Native template supplies its shell permission.

```bash
rn-logs apps                                  # list apps connected to Metro
rn-logs logs --app <name>                     # follow logs for that app
rn-logs logs --app <name> --limit 50          # snapshot last 50 lines then exit
rn-logs logs --app <name> --verbose           # include full stack traces
```

Notes:
- Read the assigned Metro port from `splashdown.env`, then pass it to `rn-logs` with
  `--port <n>`.
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

- Run `loadout sync` in the project to refresh template instructions, permissions, and skills
  for its configured harnesses.
- Install `rn-logs-cli` globally for log streaming (`npm install -g rn-logs-cli` or
  `bun add -g rn-logs-cli`). Device-automation setup is covered in the shared mobile guidance.
