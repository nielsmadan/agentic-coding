## Sub-Agent Dispatch

Sub-agents are the fastest way to spend a lot of tokens without the user seeing it coming. Three rules, in priority order.

**Three at a time, then ask.** Launch at most **3** sub-agents in parallel for a task. If the work genuinely needs more, stop and ask first — name the exact count, what each one covers, and why fewer will not do. Wait for an answer. This applies to a skill that specifies a larger fan-out too: the skill's design does not pre-authorize the spend, so still ask, using its list as the proposal. Sequential rounds count toward the same budget — three now and four more after the first batch returns is seven, not three.

**Dispatch read-only unless the agent must write files.** Use an agent type with no agent-spawning tool of its own — Claude Code's `Explore` or `Plan`, or any harness's read-only agent profile. These keep Bash, search, fetch and MCP tools, so research and review agents lose nothing. A general-purpose agent inherits the full toolset *including the ability to spawn more agents*, and will happily decompose a broad brief into its own fan-out — two rounds of that turns 5 agents into 20.

**When an agent must be write-capable, tell it not to recurse.** Put a literal line in its prompt: *"Do not dispatch sub-agents; do this work yourself."* This is the only guard available once read-only is off the table.

Two habits that keep the budget honest: give each agent **one question**, not a six-part brief that invites decomposition; and report the cost when you are done — how many agents ran and roughly what they consumed — so the next decision is an informed one.
