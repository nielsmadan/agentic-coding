## macOS VM testing (Tart)

Clean-install, release and UI tests that must not touch the host run in a disposable Tart clone
of a shared base image. Load the `macos-vm` skill before the first `tart` command: it owns the
VM lifecycle, guest control and cleanup. The project's `docs/tests/` owns what to test.

- **Fork the shared base, never use it directly.** `base-macos-27` (macOS 27.2) is the base
  for every project. Clone it per run as `<project>-<purpose>-<YYYYmmdd-HHMMSS>`. A clone is
  instant, starts at zero extra disk, and only the guest's own writes take space. A whole test
  run typically costs a few hundred MB. `tart list` reports logical sizes; they are not disk use.
- **Leave `base-*` VMs and the OCI cache alone.** Do not boot, modify, rename or delete a base.
  Do not pull an image or build a new base unless the user asks: each costs tens of GB.
- **Two macOS guests at most, machine-wide.** Virtualization.framework refuses a third at
  start; it does not queue. Check `tart list` for `running` VMs first. If two are running, wait
  or tell the user. Never stop a VM your session did not start.
- **Delete your clone when the task ends**, including after a failed run. Keep it only when the
  user asks, and name it in your final report. A guest kept for reuse (signed in, app
  configured) is a clone the user asked for. Record its name in the project's test docs.
