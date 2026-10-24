# Subagent prompts

Fill the `{…}` slots. Every prompt ends with the same delegation guard, because
these workers must not fan out further.

## Session reader

```
You are reviewing how the agent skill `{name}` performed in real sessions.
The skill's current source is {skill_path}/SKILL.md; read it first.
Its edit history (newest first):
{git_log}

For each session below, read the transcript with
  python3 {repo}/loadout/skills/check-agent-logs/scripts/search_agent_logs.py --read {ref}
(add --offset N to continue a truncated read; use --mode log only if the
answer is in tool output). Sessions: {refs}

Find moments where the skill failed the user:
- the user corrected, redirected, or overrode the agent
- the agent called something blocked, impossible, or out of scope that a
  reasonable step would have solved
- the agent skipped, reordered, or misread a step, or guessed where the skill
  was ambiguous
- the skill loaded when it should not have, or was clearly needed and not loaded

For each finding return:
- ref and approximate timestamp
- the user's words, quoted verbatim, if they prompted it
- what the agent did, and what it should have done
- the SKILL.md line or section responsible, or "not covered"
- whether a commit in the edit history after that date already addresses it

Return "no issues" for a session with none. Report only what the transcript
shows; do not speculate about sessions you did not read. Do not edit files.
Do not dispatch sub-agents or launch other agent CLIs; do this work yourself.
```

## Trigger test

Build the prompts yourself before dispatching: 8-10 should-trigger (formal and
casual phrasings, a case that never names the skill, a case where it competes
with a neighbour and should win) and 8-10 near-misses that share its keywords but
belong to another skill or to none. Obviously unrelated negatives test nothing.
Make each prompt substantive; one-step requests skip skills regardless of the
description (per Anthropic's own `skill-creator`).

```
Below is the list of skills an agent can load, as name: description.
For each numbered user request, answer with the single skill you would load
before starting, or "none" if you would just do the task, plus a reason of at
most one line. Judge only from the descriptions.

Skills:
{listing}

Requests:
{numbered_prompts}

Do not dispatch sub-agents or launch other agent CLIs; do this work yourself.
```

Score it against your expected answers. This approximates the harness's choice
from the same listing; it does not reproduce it.

## Dry run

Write the expected behaviours (3-6 checkable statements) before dispatching, so
the results cannot shape them.

```
You are testing whether an agent skill's instructions are clear. Read
{skill_path}/SKILL.md and any file it tells you to read, then handle this
request as if a user had just sent it, in {cwd}:

  {prompt}

{mode_line}

Report:
1. The ordered actions you took or would take, with the commands.
2. Every decision point, which branch you chose, and the instruction that
   decided it.
3. Every place you had to guess, found two instructions in tension, or needed
   something the skill never told you how to get. Quote the lines.
4. Anything in the skill you would skip as unnecessary.

Do not dispatch sub-agents or launch other agent CLIs; do this work yourself.
```

`{mode_line}` is one of:

- **Read-only skill:** "Carry out the request for real. Do not modify files."
- **Anything with side effects** (edits, commits, network sends, interactive
  handoffs): "Do not execute anything that changes files, git state, running
  processes, or anything outside this machine. Read freely; describe the rest."
