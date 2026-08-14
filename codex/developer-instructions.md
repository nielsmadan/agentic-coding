`Operation not permitted`, `EACCES`, `EPERM` or a `Sandbox denial` footer usually does NOT mean a missing nono grant. Verify before concluding, and never offer a grant as the first remedy.

1. Did the command actually fail? nono prints `Sandbox denial: N paths blocked` at exit even on successful runs, listing harmless config probes. Check the exit code and real output first.

2. Can you quote a path from the error output? If not, you have a guess, not a denial. Never report a blocked path you did not read in the output.

3. Verify that exact path with `nono why --self --path <path> --op read|write|readwrite`. `--self` is required: without it nono why evaluates the DEFAULT profile and reports DENIED for almost anything, even outside a sandbox. It also reports DENIED for a granted path under `~/Library/Keychains`, which in fact reads fine. If it says denied but the command works, believe the command.

Most such failures are a tool sandboxing itself. Seatbelt cannot nest, so `sandbox-exec: sandbox_apply: Operation not permitted` — or any error naming a path `nono why --self` says is allowed — means an inner sandbox, which no grant will fix. Disable it: `swift` takes `--disable-sandbox`; `xcodebuild` takes `-IDEPackageSupportDisableManifestSandbox=1 -IDEPackageSupportDisablePluginExecutionSandbox=1`; Chrome takes `--no-sandbox`. Codex's own is already disabled by the wrapper.

A profile change never reaches a running session — Seatbelt applies policy at process start. If a grant was added after this session began, say it needs a restart rather than requesting it again.

If it is a genuine denial: state the path and the `nono why --self` verdict, and stop. Do not suggest `nono run --allow` or `nono profile promote` — profiles are version-controlled in ~/ac/nono/ and edited there. Adding a grant is the user's decision. Never work around it by relocating files, weakening a test, or asking another session to read the path.
