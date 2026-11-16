## Process diagnostics

When it is unclear what launched a process, owns a port, or keeps restarting, start with
`witr --pid <pid> --json` or `witr --port <port> --json`. Use `witr --file <path> --json`
for a file holder and `witr --pid <pid> --tree` for ancestry. Avoid `--env`, which exposes
process environment variables. If witr is unavailable or inconclusive, follow up with
`ps`, `lsof`, `launchctl`, or the launch logs; ancestry cannot recover an exited parent.
