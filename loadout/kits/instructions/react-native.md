## React Native project tooling

Use `kits = ["react-native"]` in `loadout/config.toml`. This kit includes shared
mobile device automation, the shared React guidance, and a project-scoped upgrade skill.

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

### JavaScript logs (`agent-device logs`)

Read JavaScript runtime output with `agent-device logs`. In development builds, React Native
writes `console.log`/`warn`/`error` to the platform log, which is what it streams: on Android
under the `ReactNativeJS` logcat tag, on iOS under `com.facebook.react.log:javascript`.

```bash
agent-device logs clear --restart     # start a clean capture for the open session
agent-device logs mark "before submit"
agent-device logs path                # then grep that file, never read it whole
grep -n -E "ReactNativeJS|react.log:javascript" <path>
```

For components that logged errors or warnings while rendering, use
`agent-device react-devtools errors`. For native crashes, see `help debugging` (`debug symbols`).

### When to reach for the deployed skill

- **`/rn-upgrade`** — bumping the React Native SDK or doing a major version migration
  (e.g., 0.83 → 0.84). It fetches the upgrade diff, identifies breaking changes, and walks
  through native-side adjustments. Don't invoke it for routine dependency bumps
  (`yarn upgrade-interactive` covers minor JS deps).

### Notes

- Run `loadout sync` in the project to refresh kit instructions, permissions, and skills
  for its configured harnesses.
- Device-automation setup is covered in the shared mobile guidance.
