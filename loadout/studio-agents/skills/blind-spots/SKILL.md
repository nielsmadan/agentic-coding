---
name: blind-spots
description: Surface consequential decisions a plan, design, or research brief left silently assumed, recommend an answer to each, and get them settled without waiting on Niels — by the project's lead, with second opinions on consequential ones, and one batch to Niels per run for disagreements and decisions reserved for him. Use when a workflow (longshot, brainstorm, evaluate-tech, release-review, research-general, research-tech) calls `blind-spots`, or a task says "blind spots", "stress-test this plan", "poke holes in this", "what am I missing", "what haven't we decided". Do NOT use for a clear factual lookup, to generate ideas when it is unclear what to build (use `ideation`), or to review an already-written plan with agents (use `review-plan`).
argument-hint: '[plan, design, idea, or research brief to probe; blank = take it from the task]'
effort: high
---

# Blind Spots

Understand the intended outcome, challenge the framing, then find the decisions the
plan left open and get each one settled by whoever owns it.

A plan or research brief can feel complete because its gaps were filled in silently.
Make those decisions visible before they steer implementation or research. Nobody
watches this session, so the questions do not go to a person waiting at a prompt:
they go to the project's lead, and Niels hears only about disagreements and the
decisions reserved for him.

The two routes this uses, to the lead and to Niels, are in your global instructions
under "Settling Open Questions".

## Instructions

### 1. Resolve the target

The argument is what to probe. If blank, take it from the calling workflow's brief or
your task. If no target is in play, return that to the caller or report it; do not
invent one.

### 2. Recon before deciding anything

A question the context could have answered wastes the lead's round. Before writing any
decision, read the available context: the task and its brief and relevant supplied
documents; for repo work, the source, `AGENTS.md` / `CLAUDE.md`, and relevant `docs/`.
Reuse recon and settled decisions supplied by a calling workflow. For an unfamiliar
topic, a short direct lookup can establish the terminology or options needed.

**Finding facts is your job, never the lead's.** Anything discoverable from the
filesystem, the git history, or a tool is yours to look up. What goes to the lead is
intent, priorities and decisions that the available context cannot establish. Open
empirical questions remain research tasks; they need not be settled before research
begins.

### 3. Build the decision tree, then prune it

**First, check the target is one piece of work.** A brief describing several
independent subsystems needs splitting before it needs decisions. Propose the split
and the order as the first decision, and probe only the first piece.

**Establish intent before narrowing.** Reflect the intended outcome, who it serves,
and what success means, as the task and brief state them; keep their statements apart
from your assumptions. Where intent is unclear, that is the first decision to send,
with your best reading as the recommendation.

**Challenge the framing once.** Consider a simpler way to achieve the outcome, a
materially different mechanism, and whether a presumed constraint is actually required.
Use a relevant lens from `ideation` when useful: inversion (what would make this fail?),
analogy (how does another domain solve this?), or removing one assumed constraint.
Generate candidates before judging them. Surface only credible alternatives that could
change the outcome, with trade-offs and a recommendation; do not invent options to fill
a quota. Respect explicit constraints and settled choices unless new evidence challenges
their rationale.

Then map the work as decisions, each branching into the decisions that hang off it.
Sweep the categories below rather than working from intuition:

- **Building something** — purpose, constraints, success criteria; then the shape:
  component boundaries and interfaces, where state lives and how data moves, failure
  behaviour, and what counts as tested.
- **Researching something** — purpose, population, region, timeframe, and the outcome
  being compared.

Most categories come back already settled, by the context or by a default nobody
would argue with. The sweep exists to catch the ones that do not.

- **Keep** a decision that changes the work — different answers lead to different
  user outcomes, workflow, structure, interfaces, candidate pools, evidence to gather,
  or success criteria.
- **Cut** scope the brief carries that its stated purpose does not require: send
  "is this wanted?" as a decision instead of designing around it.
- **Drop** a decision that is cheap to reverse and constrains nothing downstream.
  Decide those yourself during the work.

### 4. Write each kept decision up and classify it

```
**D1 — <short title>** [reserved | consequential | ordinary]
<the question, with the options if it is a choice>
➡️ <recommended answer> — <why> — cost if wrong: <what breaks or must be redone>
```

- **reserved** — Niels decides it, never an agent: a big new feature, including
  the start of a longshot run on one, and anything the task, the repo's instructions
  or the lead's role reserves for him. A package to install is not a decision; it
  goes through the package gate.
- **consequential** — a wrong answer is costly: architecture, a public interface or
  persisted format, user-visible behaviour, a repo boundary, or anything expensive
  to reverse.
- **ordinary** — every other kept decision.

Order the batch by dependency. A decision whose answer depends on another open one
waits for the next batch. More than about seven decisions means the tree is split too
fine; prune again.

### 5. Settle them

**If you are the project's lead** (your launch brief says which role you have):

- **ordinary** — decide it.
- **consequential** — run `second-opinion` on it first, with the brief, the options and
  your recommendation, so two other models weigh in. When you and they end up agreeing,
  that is the ruling. When they still disagree after you have weighed their reasons,
  your answer becomes a provisional ruling that goes into Niels's batch. Work continues
  on it unless its cost if wrong is irreversible; then the work that depends on it waits
  for Niels and the rest continues.
- **reserved** — never decide it. It goes into Niels's batch with your recommendation,
  and the work that depends on it waits. A longshot run on a big new feature does not
  start without his approval.

**If you are not the lead:** send the batch to your lead by the lead route, with your
recon summary so the lead does not redo it, and wait for its rulings. The lead
forwards reserved decisions to Niels. While waiting, continue independent read-only
work.

A sent batch stays pending until rulings come back. Silence, elapsed time and the
route's delivery receipt settle nothing. When a route is missing, that is a blocker:
report it, as your global instructions say; do not settle the batch yourself.

### 6. Record every ruling

```
Ruling: <decision> — <why> — <cost if wrong> — decided by: <who>
```

`<who>` is `lead`, `lead + second-opinion (<model>, <model>)`, `lead, provisional;
disputed, sent to Niels`, or `Niels`. Write rulings into the calling workflow's ledger
when it keeps one, such as longshot's; otherwise into the brief you return or the
task's result.

### 7. One batch to Niels per run

The lead collects the disputed and the reserved decisions and sends them by the Niels
route in one message when the pass closes, never one at a time. Each item carries the
question, the options, the lead's answer, what the other models said when it was
disputed, the cost if wrong, and what is waiting on it. When Niels answers, his answer
replaces the provisional ruling as `decided by: Niels`, and the lead has the work that
built on a different answer redone.

### 8. Close

Stop when the intended outcome is understood, the framing has been challenged,
credible alternatives have been considered, and every consequential decision is
settled or waiting on Niels. Unknown facts may remain.

Return a compact brief to the caller: purpose, scope, settled constraints and
priorities, alternatives considered and why the chosen approach fits, the rulings with
who decided each, what waits on Niels and what is blocked on it, and remaining factual
questions. If the context already settles everything, return immediately. The caller
owns its own approval steps; do not add a closing confirmation. Invoked directly by a
task, put the brief in the task's result.

## Boundaries

- **Do not build during the pass.** No edits, no scaffolding, no mutating commands, no
  implementation subagents. Reading and searching are expected.
- Cap parallel lookups at **three read-only subagents**, one question each. The lead's
  `second-opinion` calls are not lookups and do not count against this.
- Never call `AskUserQuestion` or wait on a prompt meant for a person at the keyboard.
- Do not re-send a decision already ruled on, in this run or in the docs.

## Examples

### An implementer's longshot run

`longshot add team workspaces` in an implementer session. Recon finds single-tenant
auth. The batch to the lead: one decision for many workspaces per user (consequential),
one for migrating or grandfathering existing data (consequential), one for invites by
email or by link (ordinary), and one for moving billing to the workspace. Billing on
the workspace is a big new feature, so it is reserved. The lead rules on invites
directly, and runs `second-opinion` on the two consequential ones. The models agree on
many workspaces, but not on migration, so that ruling is provisional. The billing
decision and the migration dispute reach Niels as one batch. Longshot's run waits on
the billing decision, because it is the start approval for a big feature.

### A research brief

`research-tech` calls this on "pick a queue for the job runner" in a lead session.
Purpose and constraints are in the task; the only open fork is whether jobs must
survive a restart. Consequential, so the lead runs `second-opinion`, they agree on
durable jobs, and the ruling goes back in the returned brief. Niels gets nothing.

## Troubleshooting

### Everything ends up in Niels's batch

"Reserved" was read too broadly. It covers big new features and what is explicitly
reserved for him; an uncertain call is consequential, not reserved.

### The lead route or the Niels route is not there

It is a placeholder until the fleet's messaging exists. Report it as a blocker with
the batch attached; do not decide on the lead's or Niels's behalf.

### A decision turns out to depend on one already ruled

Apply the ruling, drop the decision, carry on.
