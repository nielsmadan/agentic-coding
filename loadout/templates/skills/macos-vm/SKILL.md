---
name: macos-vm
description: Use the shared local macOS VM (tart) to test that an app downloads, installs and integrates, or to try a dev tool or agent plugin in a clean macOS. Use before running `tart pull` or `tart clone ghcr.io/...` — a base image is already downloaded on this machine and pulling another costs ~25 GB and an hour.
effort: low
---

# macOS VM (tart)

A macOS base image is **already downloaded** on this machine. Clone it; never pull your own.

## Never pull

```sh
tart list
```

The `OCI` row is the shared base image (~25 GB, in `~/.tart`). Cloning it is **free** — measured
at 0 MB for a 29 GB VM, because APFS clones copy-on-write and only diverge as they are written
to. **Never run `tart pull` or `tart clone ghcr.io/...`** unless the user explicitly asks for a
new image.

## Check memory before booting

RAM is the constraint, not disk. Guests are configured for 8 GB.

```sh
sysctl -n kern.memorystatus_vm_pressure_level    # 1 = normal, 2 = warn, 4 = critical
```

At level 2 or above, say so and stop — a VM started under pressure gets OOM-killed and can take
the user's own processes with it. One guest at a time. `tart set <vm> --memory 4096` lowers the
allocation.

## Drive the guest with `tart exec`, not SSH

The base image ships `tart-guest-agent`, so `tart exec` runs commands directly as `admin`. It
needs no password, no key and no `expect`:

```sh
tart exec <vm> /bin/sh -c 'sw_vers -productVersion'
```

Prefer it over SSH always. SSH into the guest is password-only (`admin`/`admin`), `~/.ssh/config`
is a permanently-restricted path so ssh needs `-F /dev/null`, and **`scp` is blocked by nono
outright** — driving it through `expect` is fragile and wasted an hour of a previous session.

## Move files with `--dir`

Share a host directory at boot; it appears in the guest under `/Volumes/My Shared Files/`:

```sh
tart run --no-graphics --dir=shared:/abs/host/dir <vm> &
tart ip --wait 150 <vm>
tart exec <vm> /bin/sh -c 'echo hi > "/Volumes/My Shared Files/shared/out.txt"'
```

Read-write in both directions, verified. This is how files leave the guest, since `scp` is
blocked.

## Screenshots: two routes

`screencapture` through `tart exec` returns the **real desktop** — the base image pre-bakes the
TCC Screen Recording grant, so no provisioning is needed:

```sh
tart exec <vm> /bin/sh -c 'screencapture -x "/Volumes/My Shared Files/shared/desktop.png"'
```

Verified: 2048x1536, a live Sequoia session auto-logged-in as `admin`. A missing grant would give
an all-black frame of a few KB instead — check the file size.

## Input: use VNC, never osascript

**In-guest synthetic input does not work and cannot be made to work without reprovisioning.**
`osascript` driving System Events fails `-1712 AppleEvent timed out` then `-609 Connection is
invalid` (no Accessibility grant), and `cliclick` is not installed. Do not go down that road.

**Drive the guest over VNC instead.** Input arrives as virtual HID events from the hypervisor
rather than as synthetic events posted inside the guest, so macOS's Accessibility gate never
applies — no TCC writes, no SIP disabling, guest stays stock:

```sh
tart run --vnc-experimental --no-graphics <vm> &
# the log prints: VNC server is running at vnc://:<password>@127.0.0.1:<port>
```

Then drive it with `vncdotool`. `~/.local/share/uv/tools` is not granted, so redirect uv's
directories into the workspace rather than asking for a grant:

```sh
env UV_TOOL_DIR="$PWD/uvtools" UV_CACHE_DIR="$PWD/uvcache" \
  uvx --from vncdotool vncdo -s "127.0.0.1::<port>" -p "<password>" \
  move 61 23 pause 1 click 1 pause 2 capture shot.png
```

Verified from inside the sandbox: `capture` returns the framebuffer, `move`+`click` opened the
Apple menu, and `key esc` closed it again.

One rough edge: the command-key modifier. `super-space` and `lsuper-space` do **not** trigger
Spotlight — plain keys and clicks are reliable, the cmd modifier spelling still needs working
out. Prefer clicking menus over keyboard shortcuts until it is.

Present in the guest: `curl`, `hdiutil`, `open`, `osascript`, Safari, `brew`.
Absent: `cliclick`, `displayplacer`, `ffmpeg`.

So a download/install/integrate test is: script the fetch and install with `curl`/`hdiutil`/`cp`,
`open` the app, then **verify by screenshot** — falling back to VNC clicks for anything that needs
a real GUI interaction, such as an installer wizard or a permission dialog.

## Guests are disposable

If a guest gets into a bad state, do not repair it — throw it away. Re-cloning costs 0 bytes and
no time:

```sh
tart stop <vm>; tart delete <vm>; tart clone <local-base> <vm>
```

## Inside the sandbox

All of the above works under nono. `$HOME/.tart` is granted and the Seatbelt rule
Virtualization.framework needs is in `agent-common.json`. Two denials appear and block nothing:
`~/Library/HTTPStorages` while pulling, and `~/.ssh/id_*` when ssh tries its default keys.
Neither should be granted.

A session started before those grants landed will not see them — Seatbelt applies policy at
process start. Say it needs a restart rather than reporting a denial.
