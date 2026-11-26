## Sub-agent Models

Pass both `model` and `reasoning_effort` on every `spawn_agent` call. A spawn without them inherits this session's model and effort, usually the top tier, so routine work runs at top-tier cost without anyone choosing that.

Skills name tiers in Claude Code's terms. Here they map to:

| Skill says | `model` | `reasoning_effort` |
|---|---|---|
| `haiku`, low | `gpt-6.2-sol` | `low` |
| `sonnet`, mid | `gpt-6.2-sol` | `medium` |
| `opus`, high | `gpt-6.2-sol` | `max` |

Where a skill names no tier for a role, use high for implementing a design-level task and for a first-pass review, and mid for reconnaissance, research, docs edits, fixes, scoped re-reviews and scoring findings. Spawn on `gpt-6.2-astra` only when the user asks for it: it backs the xhigh and max tiers, two to two and a half times the cost of Sol at `max` for a few benchmark points.
