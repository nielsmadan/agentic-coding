# Shared base image

`base-macos-27` was built on 2026-11-13 with Tart 2.41.1 on a macOS 27.2 host. It is a clone
of `ghcr.io/cirruslabs/macos-golden-gate-base:latest` (macOS 27.2, build 26B123).

## Contents

| Area | State |
|---|---|
| Account | `admin`, auto-login, passwordless `sudo`; `tart exec` runs as this user |
| Disk | 80 GB virtual (ASIF, sparse), about 33 GB free in the guest |
| Toolchain | Command Line Tools with Swift 6.4.2, `clang`, `git`, `/usr/bin/python3`; Homebrew in `/opt/homebrew`. No Xcode |
| Apps | iTerm2 3.7.7 with Enable Python API on and its uv Python runtime installed; Claude Code 2.1.311 (Homebrew cask; not signed in) |
| CLI | `cliclick` for mouse input |
| Updates | macOS automatic download/install and App Store updates off; iTerm2 update checks off |

Already granted in the guest, so a clone shows no prompt for these:

- Accessibility, Screen Recording and PostEvent for `tart-guest-agent`, `osascript` and the
  Python.org bundle (these come with the Cirrus image)
- Automation of System Events and iTerm by `tart-guest-agent`
- `screencapture`'s private-window-picker bypass, Gatekeeper first-open of iTerm2, and iTerm2's
  local-network access

Commands launched through `tart exec` count as `tart-guest-agent` for these permissions. A
helper you compile or install inside a clone does not inherit them; use the tools above
before you build your own.

A clone of this base reaches the desktop about 30 seconds after `tart run`.

## Not in the base

The base does not include project apps and their defaults, signed-in accounts, Xcode, or
per-app notification styles. A notification setting such as Banners for an app can only be
set once that app is installed and has asked for permission. Do it in the clone through the
GUI, or keep a prepared clone the user asked to keep.

## Rebuilding or adding a version

Only rebuild when the user asks: a new image costs tens of GB of downloads. Name it
`base-macos-<major>`, follow the same steps, then update this file and the kit's instructions.

1. `tart clone ghcr.io/cirruslabs/<image>:latest base-macos-<major>`, then
   `tart set base-macos-<major> --disk-size 80`. The Cirrus image grows its APFS container
   on the next boot.
2. Boot with `tart run --no-graphics --no-audio --vnc-experimental`. Approve each dialog from
   a VNC screenshot ([VNC fallback](interaction.md#vnc-fallback)). Dialogs appear only when a
   command first needs them, so do each step and check the screen afterwards.
3. Run an `osascript` that talks to System Events and allow the Automation dialog. Run
   `screencapture` and allow the bypass prompt.
4. `brew install --cask iterm2 claude-code` and `brew install cliclick`. Write
   `defaults write com.googlecode.iterm2 EnableAPIServer -bool true` and
   `SUEnableAutomaticChecks -bool false`. Open iTerm2, choose **Open** and **Allow**, then use
   **Scripts → Manage → Install Python Runtime** and confirm the download.
5. Run `scripts/iterm.py --vm <base> list` and allow "tart-guest-agent wants access to control
   iTerm".
6. Turn off updates: under `/Library/Preferences/com.apple.SoftwareUpdate` set
   `AutomaticDownload` and `AutomaticallyInstallMacOSUpdates` to false, and under
   `com.apple.commerce` set `AutoUpdate` to false.
7. Quit iTerm2, `brew cleanup -s`, remove shell history and temporary captures, and shut down
   from inside the guest. Smoke-test one clone (boot, `iterm.py list`, `cliclick`,
   `screencapture`), then delete it.
