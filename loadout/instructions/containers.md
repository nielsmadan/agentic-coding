## Containers (Colima)

Docker runs inside a [Colima](https://github.com/abiosoft/colima) VM. There is no Docker Desktop
on this machine — telling the user to start it is always wrong. Sandboxed agents reach the daemon
through one granted socket, `~/.colima/default/docker.sock`, and that socket is the only part of
Colima they can touch.

**Recognise a stopped VM immediately.** Either of these means the Colima VM is not running. It is
not a sandbox denial, not a missing grant, and not a fault in the command you ran:

```
Cannot connect to the Docker daemon at unix:///Users/nielsmadan/.colima/default/docker.sock. Is the docker daemon running?
failed to connect to the docker API at unix://.../docker.sock; ... connect: no such file or directory
```

The wording differs between docker CLI versions; both mean the same thing. Do not retry the
command, rewrite it, reach for a different compose file, or open a `nono why` investigation —
none of that can help. Report it and hand the fix over.

**A sandboxed session cannot start it, and no grant should be added for this.** `~/.colima` and
`~/.lima` are denied for both read and write, so `colima start` cannot work. That is deliberate:
`~/.colima/default/colima.yaml` holds the VM's `mounts:` list, which is the control that stops the
VM mounting all of `$HOME`. An agent able to write there could mount the whole home directory into
a container and walk straight out of the sandbox. Ask the user instead, in one line:

> Docker isn't reachable — the Colima VM is down. Run `colima start` in your own terminal and I'll retry.

Not `! colima start`: the `!` prefix runs the command inside this session's sandbox, where it fails
on the same `~/.colima` denial.

**Do not run `colima status` or `colima list` from a sandbox to confirm the diagnosis.** Both need
`~/.colima`, and `colima status` fails there with `cannot make required directory: mkdir
/Users/nielsmadan/.colima/_lima: file exists` — a permission error misreported as corruption.
Passing that on as a Colima fault sends the user after the wrong problem. The liveness check that
does work sandboxed is the socket itself:

```sh
docker version --format '{{.Server.Version}}'
```

**An unsandboxed session may start it.** `claude` and `codex` run raw inside `~/ac` and `~/rc`, so
there `colima start` is yours to run. This machine loads no `brew services` autostart for colima;
on a machine that does, starting by hand makes launchd respawn the job every 10 seconds.

**`colima list` reporting `Running` does not mean the daemon is up.** The lima hostagent keeps
reporting `Running` after the VZ VM dies and leaves a stale `docker.sock` behind, so every `docker`
command fails while Colima insists it is fine — once for two days before anyone noticed. The fix is
`colima stop --force` then `colima start`; a plain `colima stop` cannot stop a VM that is not
answering. The full signature and its log evidence are in `~/rc/AGENTS.md`, which is readable only
from an unsandboxed session.
