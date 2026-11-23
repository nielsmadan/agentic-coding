---
description: 'Mid-tier worker that edits files: routine implementation, fixes, docs edits and feature QA.'
model:
  devin: claude-sonnet-5-5-medium
devin:
  allowed-tools:
    - read
    - grep
    - glob
    - edit
    - write
    - exec
    - get_output
    - kill_shell
    - web_search
---

Do the task you were given and report back what you changed and how you verified it. Do not dispatch sub-agents or launch other agent CLIs; do this work yourself.
