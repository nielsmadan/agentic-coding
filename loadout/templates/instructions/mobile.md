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

Both platforms can be built, installed and driven on a real device from inside the sandbox,
with the project's normal signing settings.

**Save the full build log to a file and search it.** Never pipe a build through `tail` or
`head`: an Xcode or Gradle failure summary names only the step that failed (`CodeSign …`,
`:app:mergeDebugResources`), and the real cause sits hundreds of lines earlier.

```sh
xcodebuild … > build.log 2>&1; grep -nE 'error:|errSec|warning: .*sign' build.log
```

**Android.** `adb` reaches a paired device from inside the sandbox, including `shell`,
`install` and `reverse`, and debug builds are unsigned:

```sh
adb devices                                   # confirm the device is attached
./gradlew installDebug                        # or: adb install -r <path>.apk
adb reverse tcp:8081 tcp:8081                 # dev server reachable from the device
adb logcat -T 200 | grep -i <tag>
```

**iOS — the project's own signing settings work, automatic included.** The sandbox cannot read
the login keychain. It can read `~/Library/Keychains/agent-signing.keychain-db`, which is on the
default keychain search list and holds the Apple Development identities agents sign with. Xcode
finds them on its own: no `CODE_SIGN_IDENTITY`, `OTHER_CODE_SIGN_FLAGS` or `--keychain` override
is needed, and no `-allowProvisioningUpdates` either (Xcode's account login lives in the denied
login keychain, so let it use the profiles already installed).

Check what the sandbox can sign with directly:

```sh
security find-identity -v -p codesigning      # the identities available to this session
```

Never probe the keychain with `security show-keychain-info`: when the keychain is locked it
waits forever on an unlock dialog no sandboxed process can answer. Do not trust `ls` or
`nono why` on `~/Library/Keychains` either — both report the directory as denied while the
granted keychain file inside it works.

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
alike from inside the sandbox. On iOS it builds its own signed XCTest runner, which signs the
same way; `agent-device prepare ios-runner` has been verified on a physical iPhone from inside
the sandbox.

### When a device step fails

Match the symptom before concluding anything. Most of these are not missing grants, and two
of them you fix yourself.

| symptom | what it actually is | what to do |
|---|---|---|
| `CodeSign …` fails, `errSecInternalComponent`, or the build hangs at signing | usually `agent-signing.keychain-db` is locked (it raised an unlock dialog nobody in the sandbox sees), or its certificate chain needs refreshing | run `security find-identity -v -p codesigning`; if the identity is listed, ask the user to unlock it: `security unlock-keychain -p "" ~/Library/Keychains/agent-signing.keychain-db` in their own terminal. If it is missing, ask them to run `~/ac/sync.sh` |
| `No signing certificate … with a private key was found`, or `0 valid identities` | the team's identity is not in `agent-signing.keychain-db` | check the team's certificate against `find-identity`; importing one is the user's call |
| `<Pod> does not support provisioning profiles` | you passed `PROVISIONING_PROFILE_SPECIFIER` on the command line | **fix it yourself** — drop the flag; it applies to every target |
| `"<App>" requires a provisioning profile` | no matching profile installed for the bundle id | project configuration; fails identically outside the sandbox |
| a denial for a path that *is* granted | a stale Gradle daemon holds the old Seatbelt policy | **fix it yourself** — `./gradlew --stop`, or pass `--no-daemon` |
| `NDK not configured` while the NDK is installed | the SDK is unreadable | report it as a missing grant, not a missing install |
| `Failed to create parent directory '~/.gradle/<name>'` | Gradle made a new top-level directory that is not granted | report the exact path; it needs a grant plus seeding |
| an error naming a path `nono why` says is **allowed**, that no grant fixes | a blocked *system service*, which carries no path | ask the user to re-run it unsandboxed and read the footer |
| `adb devices` shows `unauthorized` | the phone has not accepted this Mac | ask the user to unlock it and accept the debugging prompt |
| `adb devices` is empty for a wireless phone, and the adb server log shows `SSLV3_ALERT_CERTIFICATE_UNKNOWN` | the wireless-debugging pairing expired | ask the user to re-pair: Wireless debugging → Pair device with pairing code on the phone, then `adb pair <ip>:<port>` |
| the device is missing from `devicectl list devices` | locked, untrusted, or Developer Mode off | ask the user to unlock and trust the Mac |

Two commands to hand the user, verbatim, when the table says to. They run in the user's own
terminal, not as `!` commands, which would run inside this sandbox. Never paraphrase them into a
description of what they should do:

```sh
# unlock the signing keychain (it has an empty password)
security unlock-keychain -p "" ~/Library/Keychains/agent-signing.keychain-db

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
