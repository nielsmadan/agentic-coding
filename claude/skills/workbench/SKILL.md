---
name: workbench
description: Run code in a Docker-sandboxed environment. Use when developing scripts that need isolation from the host, or when iterating on untrusted/experimental code.
argument-hint: <task description> [--lang <python|node|go|bash>]
---

# Workbench

Develop and iterate on code inside a Docker container with no host access.

## Usage

```
/workbench build a python script that reads a CSV and outputs summary stats
/workbench write a script that fetches data from an API and processes it
/workbench --lang node create an express server prototype
/workbench                              # Uses recent conversation context
```

## Flags

| Flag | Effect |
|------|--------|
| `--lang <language>` | Override language detection (python, node, go, bash) |
| No flags | Python (default) |

## Security Model

**Why Docker:** Running `python script.py` on the host gives the script full access to the user's filesystem, even if the script file lives in `/tmp`. Docker containers isolate execution so the host filesystem doesn't exist inside the container.

**Permission strategy:**
- `docker exec cc-workbench-*` is whitelisted (runs inside an existing container - safe)
- `docker stop cc-workbench-*` is whitelisted (just stops a container)
- `docker rm cc-workbench-*` is whitelisted (just removes a container)
- `docker info` is whitelisted (read-only check)
- `docker run` is NOT whitelisted - the user approves it once per session

The user can verify the `docker run` command has:
- Only the workspace directory mounted (`-v /tmp/workbench-xxx:/workspace`)
- No `--privileged` flag

**Remaining risks:**
1. Container escape CVEs exist (e.g. CVE-2024-21626). Keep Docker updated.
2. Output files from the workbench should be reviewed before production use.

## Workflow

### Phase 1: Setup

**1. Check Docker is available:**
```bash
docker info >/dev/null 2>&1
```

If Docker is not running, tell the user and stop.

**2. Check for stale containers from previous sessions:**
```bash
docker ps -a --filter "name=cc-workbench-" --format "{{.Names}} {{.Status}}"
```

If stale containers exist, stop and remove each by name (so commands match the whitelist):
```bash
docker stop cc-workbench-{name} && docker rm cc-workbench-{name}
```

**3. Detect language** from the task description or `--lang` flag:

| Language | Image | Exec command |
|----------|-------|-------------|
| Python (default) | `python:3.12-slim` | `python script.py` |
| Node.js | `node:20-slim` | `node script.js` |
| Go | `golang:1.22-alpine` | `go run main.go` |
| Bash | `ubuntu:24.04` | `bash script.sh` |

**4. Create workspace and start container:**
```bash
WORKSPACE=$(mktemp -d /tmp/workbench-XXXXXX)
echo "Workspace: $WORKSPACE"
```

Start the container. **This requires user approval** (not whitelisted):
```bash
docker run -d --name cc-workbench-{session_id} \
  --memory 512m --cpus 1 \
  -v $WORKSPACE:/workspace \
  -w /workspace \
  {image} \
  tail -f /dev/null
```

Use a short unique suffix for `{session_id}` (e.g., first 8 chars of a UUID or timestamp).

### Phase 2: Iterative Development (auto-approved)

This is the main loop. All `docker exec` commands are whitelisted and auto-approve.

**1. Write code** to the workspace using the Write tool:
```
Write tool -> $WORKSPACE/script.py
```

**2. Execute** inside the container:
```bash
docker exec cc-workbench-{session_id} python /workspace/script.py
```

**3. Read output**, fix issues, iterate. Repeat steps 1-3 until the script works correctly.

**Guidelines for iteration:**
- Write files to `$WORKSPACE` using the Write tool (this writes to the host path which is mounted into the container)
- Execute via `docker exec` (runs inside the container)
- Read output files from `$WORKSPACE` if the script produces file output
- Install packages if needed: `docker exec cc-workbench-{session_id} pip install pandas`
- **Use `docker exec` for all filesystem operations** inside the container (e.g., `docker exec cc-workbench-{session_id} mkdir -p /workspace/subdir`). Do NOT use host commands like `mkdir` or `chmod` on `$WORKSPACE` — only `docker exec` is whitelisted and auto-approved. Host commands will trigger a permission prompt.

### Phase 3: Graduation

When the script is working:

**1. Present the finished script** to the user with a summary of what it does.

**2. Ask where to copy it** in the project (or if the user wants it left in the workspace).

**3. Copy if requested:**
```bash
cp $WORKSPACE/script.py /path/to/project/script.py
```

**4. Cleanup:**
```bash
docker stop cc-workbench-{session_id} && docker rm cc-workbench-{session_id}
rm -rf $WORKSPACE
```

## Notes

- The container runs as root inside its own namespace - this is fine because it has no host access
- Files written to `$WORKSPACE` on the host appear at `/workspace` inside the container
- If the session crashes, stale containers are cleaned up on next `/workbench` invocation
- For long-running processes (servers), use `docker exec -d` for background execution and `docker exec ... curl localhost:PORT` to test
