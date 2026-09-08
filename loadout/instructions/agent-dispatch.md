## Sub-Agent Dispatch

Choose the smallest useful set of agents for independent work. Use the harness's concurrency limit and queue further work as slots become available. Additional agents or batches do not require confirmation solely because of their count. An invoked skill authorizes its documented workflow.

**Plan the delegation tree.** The main agent owns the overall scope and tracks direct agents, descendants, and advisor CLI calls. A child may delegate when its brief explicitly assigns coordination, names the subtasks, bounds the number of descendants, and gives a stopping condition. Grandchildren are fine for work that benefits from them. Descendants share that allocation; they cannot each start a fresh budget or rerun the whole parent workflow. A child needing more delegation returns that request to its parent, which may revise the allocation within the user's task.

**Default to workers that do their own task.** Give each one a focused question or deliverable and only the tools it needs. Restrict writes separately from delegation: a read-only profile does not necessarily remove spawning tools. For workers without a coordination role, exclude delegation tools where supported and include: *"Do not dispatch sub-agents or launch other agent CLIs; do this work yourself."* A worker can have write access without permission to delegate.

**Bound the work.** State what completes each assignment. Stop redundant research and cancel branches whose answers are no longer needed. Count nested skills and fresh CLI processes as part of the same work; do not use them to evade concurrency or spending limits. When nesting, leave capacity for the assigned children or perform their work locally.

Before a larger dispatch, briefly say how the work is divided, including planned nesting. For three or more agents, or multiple rounds, report how many ran and measured usage when available; do not invent a token estimate. Below that, omit the spend report.
