---
name: macos-vm
description: Provision and control a local Tart macOS VM for clean-install, release, integration, or developer-tool testing. Use for "test in the VM", "Tart", guest clipboard/input problems, or before pulling a macOS image. Reuse an existing local base; keep application-specific assertions in the project's test procedure.
effort: low
---

# macOS VM (Tart)

## Instructions

### 1. Choose the test state

Read the project's `docs/tests/` procedure for artifacts, setup, expected results, and cleanup
ownership. This skill owns VM transport and interaction; the project owns fixtures, product
UI selectors, and assertions.

```sh
tart list
sysctl -n kern.memorystatus_vm_pressure_level
```

Reuse an existing local base. Do not pull an image unless requested; an OCI name absent from
`tart list` may download tens of GB. Run one guest at a time, at memory pressure `1` (normal);
wait at `2` or `4`. APFS clones initially share disk blocks but grow with writes.

Distinguish a clean base from a prepared, authenticated guest. For repeat tests, shut down the
prepared guest before cloning it; retain the original and its login. Record this difference
instead of calling the clone a fresh install. Credentials remain private in the VM.

### 2. Clone and boot

Set `base` to the exact existing name from `tart list`; choose a new disposable `vm` name.
Set `shared` to an absolute staging directory in the workspace.

```sh
env TART_NO_AUTO_PRUNE=1 tart clone "$base" "$vm"
tart set "$vm" --memory 8192
tart run --capture-system-keys --dir="shared:$shared:ro" "$vm"
```

Keep `tart run` attached in a long-lived terminal/tool session. Use another invocation for
commands. Visible mode helps with authentication and permission dialogs. Leave clipboard
sharing enabled: do not pass `--no-clipboard` when the user needs to paste a login link into
the guest browser. `--capture-system-keys` routes shortcuts to the focused guest window.

Add `--dir="evidence:$evidence"` as a separate writable share when exporting screenshots.
Shares mount under `/Volumes/My Shared Files/<name>`. Stage executables on a read-only share;
copy applications into the guest before running them.

### 3. Establish guest command access

```sh
tart exec "$vm" /bin/sh -c 'sw_vers; printf "%s\n" "$HOME"'
```

Allow boot time and put a bounded timeout around this readiness probe. The prepared Cirrus
image includes a guest agent; vanilla images may not. Prefer `tart exec` over SSH or `scp`:
it needs no SSH credentials and supports stdin with `-i`. Quote guest shell expressions so
the guest, rather than the host, expands `$HOME`.

```sh
tart exec -i "$vm" /usr/bin/osascript - <<'APPLESCRIPT'
tell application "System Events" to get name of every application process
APPLESCRIPT
```

### 4. Use the most direct working interface

1. Use guest CLI commands for installation, files, processes, and diagnostics.
2. Use an application's API for structured input and observations. For iTerm2, use
   [the terminal helper](references/interaction.md#iterm2-terminal-input).
3. Use guest AppleScript/System Events for native UI and keys when permissions allow it;
   see [native UI control](references/interaction.md#native-ui-control).
4. Use visible guest interaction or [VNC](references/interaction.md#vnc-fallback) when
   Accessibility/Automation is unavailable, or for permission dialogs.

System Events is not universally broken: it timed out in a stock guest, but UI reads and
keyboard input worked in the prepared macOS 15.7.7 guest on 2026-09-18 with Tart 2.37.0.
Do not rewrite TCC databases or disable SIP. Grant needed permissions through the guest's
normal macOS UI, then repeat the actual operation.

### 5. Capture evidence and clean up

Read state through the product's interface as well as backend diagnostics. A delivered event
does not prove that the visible UI changed. Screenshots must exclude login pages, codes,
credentials, and unrelated windows. Inspect them locally before retaining them.

```sh
tart exec "$vm" /usr/sbin/screencapture -x "/Volumes/My Shared Files/evidence/desktop.png"
```

Screen Recording permission varies by image. A black frame is a failed observation, not an
empty desktop. Use a file share to keep large image payloads off the command transport.

Sanitize guest names, home paths, and session identifiers before exporting evidence. Preserve
identity relationships with consistent placeholders and meaningful terminal-ID prefixes.
Never retain cookies, login links, VNC passwords, or account screenshots in the repo.

Quit test processes, then shut down only the disposable guest:

```sh
tart exec "$vm" /usr/bin/sudo -n /sbin/shutdown -h now
tart list
tart delete "$vm"
```

Shutdown may disconnect `tart exec` and return nonzero; confirm `stopped` in `tart list` before
deleting. If graceful shutdown is unavailable, use `tart stop` on that exact disposable guest.
Do not delete the base or prepared source. Restore any original guest to its prior running or
stopped state. Do not discard an authenticated guest as the first troubleshooting step.

## Examples

- **Clean installer test:** clone a local base, boot with a read-only artifact share, install
  the signed release, let the user authenticate, then follow the project's checks.
- **Existing-install upgrade:** stop the prepared guest, clone it, stage the version fixture,
  run the product installer, compare state, and delete only the test clone.
- **CLI inside iTerm2:** list sessions with `scripts/iterm.py`, explicitly select the target
  ID, submit text, then read the screen. Keep product-specific assertions in the repo.

## Troubleshooting

- **Clipboard does not paste:** inspect the Tart command for `--no-clipboard`. Reboot with
  sharing enabled if necessary, focus the guest browser, and let the user paste there.
  Never put a login link into command logs or saved data.
- **System Events times out or denies access:** inspect guest Automation and Accessibility
  permissions; use visible input/VNC while resolving them. A transport timeout alone does
  not establish a macOS permission denial.
- **iTerm2 API returns 401:** use the helper's explicit AppleScript cookie/key handshake;
  verify Enable Python API and the guest approval prompt. Do not print the cookie/key.
- **Guest command channel fails:** check `tart list` and the desktop. Preserve evidence and
  distinguish transport failure from application failure. Avoid large inline captures.
- **Virtualization or filesystem denial:** apply `nono-sandbox` diagnostics to the failing
  operation. A footer probe is not proof; do not change grants or try SSH as a bypass.
