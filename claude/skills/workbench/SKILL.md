---
name: workbench
description: Run code in a Docker-sandboxed environment. Use when developing scripts that need isolation from the host, or when iterating on untrusted/experimental code.
argument-hint: <task description>
---

# Workbench

Develop and iterate on code inside a persistent Docker container with no host access.

## Usage

```
/workbench build a python script that reads a CSV and outputs summary stats
/workbench write a script that fetches data from an API and processes it
/workbench create an express server prototype
/workbench                              # Uses recent conversation context
```

## Security Model

**Why Docker:** Running `python script.py` on the host gives the script full access to the user's filesystem, even if the script file lives in `/tmp`. Docker containers isolate execution so the host filesystem doesn't exist inside the container.

**Permission strategy:**
- `docker exec cc-workbench` and `docker exec cc-workbench-*` are whitelisted (runs inside existing containers - safe)
- `docker stop/rm/start cc-workbench` and `cc-workbench-*` are whitelisted
- `docker info` is whitelisted (read-only check)
- `docker build` and `docker run` are NOT whitelisted - the user approves these once

The user can verify the `docker run` command has:
- Only the workspace directory mounted (`-v /tmp/workbench:/workspace`)
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

**2. Check if the workbench container already exists:**
```bash
docker ps -a --filter "name=^cc-workbench$" --format "{{.Names}} {{.Status}}"
```

Three cases:
- **Container is running** → skip to step 4
- **Container exists but is stopped** → restart it:
  ```bash
  docker start cc-workbench
  ```
- **Container doesn't exist** → continue to step 3

**3. First-time setup (one-time, requires user approval):**

Check if the `cc-workbench` image exists:
```bash
docker images cc-workbench --format "{{.Repository}}"
```

If no image, find the Dockerfile and build it (user approves once):
```bash
# Use Glob tool to find: **/claude/skills/workbench/Dockerfile
# Then build from that directory:
docker build -t cc-workbench /absolute/path/to/claude/skills/workbench/
```

Create the workspace directory and start the container (user approves once):
```bash
mkdir -p /tmp/workbench
docker run -d --name cc-workbench \
  --memory 512m --cpus 1 \
  -v /tmp/workbench:/workspace \
  -w /workspace \
  cc-workbench \
  tail -f /dev/null
```

After this, the container is running and all subsequent operations are auto-approved.

**4. Create a task directory** inside the container:
```bash
docker exec cc-workbench mkdir -p /workspace/{task-name}
```

Use a short descriptive name for the task (e.g., `csv-parser`, `api-client`, `etl-pipeline`).

### Phase 2: Iterative Development (auto-approved)

This is the main loop. All `docker exec` commands are whitelisted and auto-approve.

**1. Write code** to the task directory using the Write tool:
```
Write tool -> /tmp/workbench/{task-name}/script.py
```

**2. Detect language and execute** inside the container:

| Language | Run command |
|----------|-------------|
| Python | `docker exec cc-workbench python3 /workspace/{task-name}/script.py` |
| Node.js | `docker exec cc-workbench node /workspace/{task-name}/script.js` |
| Go | `docker exec -w /workspace/{task-name} cc-workbench go run main.go` |
| Bash | `docker exec cc-workbench bash /workspace/{task-name}/script.sh` |

Auto-detect the language from the task description and file extensions. No flag needed — the container has all runtimes.

**3. Read output**, fix issues, iterate. Repeat steps 1-3 until the script works correctly.

**Guidelines for iteration:**
- Write files to `/tmp/workbench/{task-name}/` using the Write tool (this writes to the host path which is mounted into the container)
- Execute via `docker exec` (runs inside the container)
- Read output files from `/tmp/workbench/{task-name}/` if the script produces file output
- Install packages if needed: `docker exec cc-workbench pip install pandas`
- **Use `docker exec` for all filesystem operations** inside the container (e.g., `docker exec cc-workbench mkdir -p /workspace/{task-name}/subdir`). Do NOT use host commands like `mkdir` or `chmod` on the workspace — only `docker exec` is whitelisted and auto-approved. Host commands will trigger a permission prompt.

### Phase 3: Graduation

When the script is working:

**1. Present the finished script** to the user with a summary of what it does.

**2. Ask where to copy it** in the project (or if the user wants it left in the workspace).

**3. Copy if requested:**
```bash
cp /tmp/workbench/{task-name}/script.py /path/to/project/script.py
```

**4. Keep the container running** for future tasks. Only clean up the task directory if asked:
```bash
docker exec cc-workbench rm -rf /workspace/{task-name}
```

## Custom Environments

If a task needs services not in the default image (e.g., PostgreSQL, Redis, Elasticsearch), create a task-specific container instead:

```bash
docker run -d --name cc-workbench-{task-name} \
  --memory 512m --cpus 1 \
  -v /tmp/workbench/{task-name}:/workspace \
  -w /workspace \
  postgres:16 \
  ...
```

This falls back to the per-task flow — the user approves the `docker run` once. The whitelisted `docker exec cc-workbench-*` pattern covers these named containers too.

## Full Cleanup

Only when the user explicitly requests it:
```bash
docker stop cc-workbench && docker rm cc-workbench
rm -rf /tmp/workbench
```

## Examples

**Prototype a CSV parser in Docker isolation:**
> /workbench build a python script that reads a CSV and outputs summary stats

Sets up (or reuses) the `cc-workbench` Docker container, creates a `csv-parser` task directory, and iterates on a Python script inside the container. Installs pandas if needed, runs against sample data, and presents the working script for graduation to the project.

**Test untrusted npm package safely:**
> /workbench try out the new csv-parse package and see if it handles edge cases

Creates a Node.js script inside the container that imports and exercises the package with various edge-case inputs. All execution stays sandboxed -- nothing touches the host filesystem or project dependencies.

## Notes

- The container runs as root inside its own namespace - this is fine because it has no host access
- Files written to `/tmp/workbench/` on the host appear at `/workspace` inside the container
- Installed packages persist across tasks (the container stays running)
- If a task needs a clean environment, use `python3 -m venv` or create a custom container
- For long-running processes (servers), use `docker exec -d` for background execution and `docker exec ... curl localhost:PORT` to test
