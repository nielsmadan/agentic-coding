## Sub-Agent Dispatch

Sub-agents are the fastest way to spend a lot of tokens without the user seeing it coming. Three rules, in priority order.

**Three at a time, then ask.** Launch at most **3** sub-agents in parallel for a task. If the work genuinely needs more, stop and ask first — name the exact count, what each one covers, and why fewer will not do. Wait for an answer. Sequential rounds count toward the same budget — three now and four more after the first batch returns is seven, not three.

**A skill you were asked to run is already authorized.** When the user invokes a skill by name and that skill specifies a fixed fan-out — `code-review`'s aspect agents, `explain`'s per-aspect writers — run its full set without asking. The invocation is the consent, and re-asking every time is friction with no information in it. Just say how many you launched. The 3-agent cap governs the count *you* choose: rows picked off a menu, an ad-hoc fan-out no skill defined, or a skill that leaves the number up to you.

**Dispatch read-only unless the agent must write files.** Use an agent type with no agent-spawning tool of its own — Claude Code's `Explore` or `Plan`, or any harness's read-only agent profile. These keep Bash, search, fetch and MCP tools, so research and review agents lose nothing. A general-purpose agent inherits the full toolset *including the ability to spawn more agents*, and will happily decompose a broad brief into its own fan-out — two rounds of that turns 5 agents into 20.

**When an agent must be write-capable, tell it not to recurse.** Put a literal line in its prompt: *"Do not dispatch sub-agents; do this work yourself."* This is the only guard available once read-only is off the table.

Give each agent **one question**, not a six-part brief that invites decomposition. Report the cost only when the dispatch was big enough to be worth knowing — three or more agents, or more than one round: how many ran and roughly what they consumed, in one line. Below that, say nothing; a spend report on every one- or two-agent lookup is noise, not budget discipline.
