## Sub-agent Models

`run_subagent` takes a profile, not a model, and neither built-in profile runs on the tier a skill asks for: `subagent_explore` gets a router-selected model and `subagent_general` this session's, usually the top tier. When a skill or these instructions dispatch a sub-agent, use one of these profiles instead:

| Skill says | Read-only work | Work that edits files |
|---|---|---|
| `haiku`, `sonnet`, low, mid | `readonly-mid` | `worker-mid` |
| `opus`, high | `readonly-high` | `worker-high` |

Where a skill names no tier for a role, use high for implementing a design-level task and for a first-pass review, and mid for reconnaissance, research, docs edits, fixes, scoped re-reviews and scoring findings. Reviewers, verifiers and scorers take a `readonly-` profile. A profile's model carries its reasoning effort, so there is no effort to pass. Roles a skill dispatches go to these profiles, not to the sidekick.
