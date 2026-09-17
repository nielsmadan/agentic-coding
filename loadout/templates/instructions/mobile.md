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

Let device commands finish inside the host tool when possible; avoid one-second
polls that each need a model turn. Combine screenshot capture and image reading in
one orchestration when supported. Batch familiar routes with selectors and expected-state
guards, stopping at states that need inspection. For feature QA, use the `qa` skill
and its native adapter for coverage, evidence, and context management.

### Setup

The `mobile`, `flutter`, and `react-native` templates select this shared guidance and the
`agent-device` shell permission for the project's configured harnesses. Run `loadout sync` in
the project after changing its templates.

Install `agent-device` globally (`npm install -g agent-device`), with Xcode for iOS and the
Android SDK + ADB for Android. Template sync supplies configuration; install these machine
prerequisites separately.

### Testing on a physical device

Both platforms can be driven on a real device from inside the sandbox. Android needs no
setup. iOS needs manual code signing configured once per project; with that in place the
sandbox behaves exactly like the host.

| | discover | build | install | drive + logs |
|---|---|---|---|---|
| **Android** | sandboxed | sandboxed | sandboxed | sandboxed |
| **iOS** | sandboxed | sandboxed, with manual signing | sandboxed | sandboxed |

**Android — nothing special.** `adb` reaches a paired device from inside the sandbox, including
`shell`, `install` and `reverse`, and debug builds are unsigned:

```sh
adb devices                                   # confirm the device is attached
./gradlew installDebug                        # or: adb install -r <path>.apk
adb reverse tcp:8081 tcp:8081                 # dev server reachable from the device
adb logcat -T 200 | grep -i <tag>
```

**iOS — use manual signing, never automatic.** Inside the sandbox
`security find-identity -v` reports `0 valid identities` even when the keychain holds one,
because enumeration goes through `securityd` rather than reading the keychain file. Automatic
signing enumerates, so it fails with *"No signing certificate … with a private key was found"*.
**That is a property of the sandbox, not a missing certificate — do not ask for one to be
imported.** Signing by explicit SHA-1 does not enumerate and works normally:

```sh
xcodebuild -workspace <App>.xcworkspace -scheme <App> \
  -destination 'generic/platform=iOS' -configuration Debug \
  CODE_SIGN_STYLE=Manual CODE_SIGN_IDENTITY=<sha1> DEVELOPMENT_TEAM=<team> build
```

Two things this needs, both one-time:

- **The identity's SHA-1**, read once from an unsandboxed shell with
  `security find-identity -v <keychain>`.
- **A provisioning profile pinned on the app target**, in Signing & Capabilities or an
  `.xcconfig`. Do **not** pass `PROVISIONING_PROFILE_SPECIFIER` on the command line: it applies
  to every target, and CocoaPods targets reject it with *"does not support provisioning
  profiles"*. Without a pinned profile the build fails with *"requires a provisioning
  profile"* — identically inside and outside the sandbox, so that error is project
  configuration, never a denial.

Installing and driving are sandboxed either way:

```sh
xcrun devicectl list devices                                  # find the UDID
xcrun devicectl device install app --device <udid> <path>.app
```

**Reaching a dev server or local backend.** A physical device is not on `localhost`.

- **Android**: `adb reverse tcp:<port> tcp:<port>` maps the device's localhost to the Mac, and
  works from inside the sandbox. It only affects device-to-host traffic — it does not prove the
  dev server is up, and it does not fix a stale bundle.
- **iOS**: there is no `adb reverse` equivalent. Point the app at the Mac's LAN address, or an
  HTTPS tunnel when the flow needs a public origin (universal links, OAuth redirects).

**Driving the app** is `agent-device` on both platforms; it sees physical devices and simulators
alike from inside the sandbox. On iOS it rebuilds its own XCTest runner, which is signed — the
same manual-signing requirement applies to the runner's target, and that combination has not
been verified.

### When a device step fails

Match the symptom before concluding anything. Most of these are not missing grants, and three
of them you fix yourself.

| symptom | what it actually is | what to do |
|---|---|---|
| `No signing certificate … with a private key was found`, or `0 valid identities` | the sandbox cannot enumerate identities | switch to manual signing; ask the user for the hash |
| `<Pod> does not support provisioning profiles` | you passed `PROVISIONING_PROFILE_SPECIFIER` on the command line | **fix it yourself** — drop the flag, pin the profile on the target instead |
| `"<App>" requires a provisioning profile` | no profile pinned on the app target | project configuration; fails identically outside the sandbox. Ask the user to pin it in Signing & Capabilities |
| a denial for a path that *is* granted | a stale Gradle daemon holds the old Seatbelt policy | **fix it yourself** — `./gradlew --stop`, or pass `--no-daemon` |
| `NDK not configured` while the NDK is installed | the SDK is unreadable | report it as a missing grant, not a missing install |
| `Failed to create parent directory '~/.gradle/<name>'` | Gradle made a new top-level directory that is not granted | report the exact path; it needs a grant plus seeding |
| an error naming a path `nono why` says is **allowed**, that no grant fixes | a blocked *system service*, which carries no path | ask the user to re-run it unsandboxed and read the footer |
| `adb devices` shows `unauthorized` | the phone has not accepted this Mac | ask the user to unlock it and accept the debugging prompt |
| the device is missing from `devicectl list devices` | locked, untrusted, or Developer Mode off | ask the user to unlock and trust the Mac |

Two commands to hand the user, verbatim, when the table says to. Never paraphrase them into a
description of what they should do:

```sh
# the signing identity's SHA-1, for CODE_SIGN_IDENTITY
security find-identity -v ~/Library/Keychains/agent-signing.keychain-db

# what the sandbox actually blocked — a sandboxed session cannot see this
nono run -p claude-local -- <the exact command that failed>
```

That second one is the only way to see nono's `Also blocked (system services)` section, which
names blocked *operations* rather than paths. A sandboxed session never sees it, and neither
`nono audit` nor `nono logs` records it. Reach for it as soon as a failure looks like the
sandbox but no grant changes the outcome — not after a second round of guessing at grants.

Everything else — discovery, `adb`, building, installing, driving and log streaming — is
expected to work sandboxed. A failure there is a real bug, a missing grant, or project
configuration, never a documented limit.
