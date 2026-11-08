# Guest interaction

These mechanisms were exercised on 2026-09-18 with Tart 2.37.0, macOS 15.7.7, iTerm2 3.6.11,
and its managed Python 3.14.0. Recheck when those dependencies change.

## iTerm2 terminal input

Install iTerm2 in the guest, use **Scripts → Manage → Install Python Runtime**, and enable
**Settings → General → Magic → Enable Python API**. Open iTerm2 before connecting. Allow its
normal API/Automation prompts in the guest. Host iTerm2 credentials are not needed.

Set `vm_skill` to the directory containing this skill's `SKILL.md` (use its loaded source path),
and `vm` to the current guest. The host needs Python 3; the helper finds a guest-managed
interpreter that imports `iterm2`. Pass `--python <guest-path>` to override discovery.

```sh
python3 "$vm_skill/scripts/iterm.py" --vm "$vm" list
session="<ID returned by list>"
python3 "$vm_skill/scripts/iterm.py" --vm "$vm" screen --session "$session"
python3 "$vm_skill/scripts/iterm.py" --vm "$vm" send --session "$session" \
  --text 'printf "vm-input-ok\n"' --submit
python3 "$vm_skill/scripts/iterm.py" --vm "$vm" screen --session "$session"
```

`runtime` prints the discovered guest interpreter path. `new-tab` creates a tab and prints
its ID; `select --session "$session"` activates a session. `list` includes `selectedTab` and
`currentWindow` so a caller can verify selection without relying on window titles.
Always inspect the selected terminal before sending text: it may contain a shell, login flow,
or interactive agent. `--submit` sends the text, waits 0.5 seconds, then sends Return separately.
Use separate text and Return events for interactive terminal applications.
Asynchronous commands need a later screen/state read; successful input only proves that the
API accepted it, not that the command completed.

The helper requests credentials inside the guest through
`iterm2.auth.request_cookie_and_key(..., AppKitApplescriptRunner)`, sets them only in that Python
process, and uses `Connection.async_create()`. It never serializes or prints the credentials.
It can trigger a guest API authorization dialog; approve it there and retry if it times out.
Treat screen output as private until reviewed, especially during authentication.

## Native UI control

Probe the permission-dependent operation, not merely whether `osascript` exists:

```sh
tart exec -i "$vm" /usr/bin/osascript - <<'APPLESCRIPT'
tell application "System Events" to return UI elements enabled
APPLESCRIPT
```

Then inspect the target process. Replace `Example` with its observed process name:

```sh
tart exec -i "$vm" /usr/bin/osascript - <<'APPLESCRIPT'
tell application "System Events" to tell process "Example"
    get name of every window
end tell
APPLESCRIPT
```

`get entire contents of window 1` discovers the accessibility hierarchy. Use narrowly scoped
reads after discovery; put product-specific selectors in that repo. Empty/loading/populated
views can have different hierarchies. Poll with a deadline instead of assuming an animation
has completed.

Keyboard events must also run inside the guest. Focus the intended app before sending keys:

```sh
tart exec -i "$vm" /usr/bin/osascript - <<'APPLESCRIPT'
tell application "System Events" to tell process "Example" to set frontmost to true
tell application "System Events" to key code 53
APPLESCRIPT
```

Automation (controlling another app), Accessibility (UI inspection/input), and Screen Recording
are separate guest permissions. A working application API does not imply System Events access.
Use the guest's **System Settings → Privacy & Security** and the actual requesting process
shown there. Do not assume the same grants exist in a different base image.

## VNC fallback

For headless work, boot with a writable evidence share and Tart's VNC endpoint:

```sh
tart run --vnc-experimental --no-graphics --dir="evidence:$evidence" "$vm"
```

Keep the printed loopback endpoint/password private. Use `vncdotool` when the native UI tool
cannot reach the VM. Redirect uv's executable/cache directories into ignored workspace storage:

```sh
env UV_TOOL_DIR="$PWD/build/vm-tools" UV_CACHE_DIR="$PWD/build/vm-cache" \
  uvx --from vncdotool vncdo -s "$vnc_address" -p "$vnc_password" \
  move 61 23 pause 1 click 1 pause 2 capture "$evidence/desktop.png"
```

Set `vnc_address` to the endpoint in `host::port` form. Do not persist the password assignment
or raw startup log. Click coordinates must come from a current screenshot, not this example.
VNC clicks and plain keys worked in the earlier stock-guest probe; Command-modifier spelling
was not established there. Use menus or working guest System Events for shortcuts.
