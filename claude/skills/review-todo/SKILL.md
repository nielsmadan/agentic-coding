---
name: review-todo
description: Turn a completed code review into a persistent, interactive todo workflow, record fix or ignore decisions and implementation plans, then implement and commit every accepted finding. Use after a review when the user invokes review-todo, says "turn this review into a todo list", "work through these review findings", supplies directives such as "fix 2, 3; ignore 7", or asks to resume review triage. Do not use to perform the original code review.
argument-hint: '[fix 2,3 | ignore 7 | resume]'
effort: high
---

# Review Todo

Turn the most recent completed review into a stateful triage-to-implementation workflow. Keep `.review-todo.md` at the repository root as the source of truth across turns and context compaction. It is temporary working state: never commit it, and remove it only after the workflow completes successfully.

## Instructions

### Step 1: Start or resume

1. Find the repository root. If the current directory is not in a Git repository, ask for the target repository before creating state; the workflow ends by committing changes.
2. Check for `.review-todo.md`:
   - If it contains an active workflow, resume it by default. Read it before using conversational context.
   - If the user clearly supplied a new review while an active workflow exists, do not overwrite it. Ask whether to resume the existing workflow or replace it with the new review.
   - If it is marked complete after an interrupted cleanup, report the recorded result and remove it.
3. For a new workflow, use the most recent completed review in the conversation or review text supplied by the user. If neither contains concrete findings, ask the user to provide or run a review.
4. Snapshot `git status --short` into the state file as the pre-existing worktree. These paths and hunks are not owned by this workflow.

An invocation may include decisions such as `fix 2, 3, 9; ignore 7`. Capture the review first so its stable IDs exist, then apply every unambiguous directive before presenting anything. Directives choose plans; they do not start code edits before triage is complete.

### Step 2: Create the state file

Normalize concrete, actionable findings into `.review-todo.md` without changing their meaning:

- Reuse unique integer IDs already shown by the review; otherwise assign stable integer IDs in its original order. Never renumber them.
- Preserve severity, title, file and line, problem, impact, proposed fix, and source when available.
- Deduplicate restatements while retaining all source labels on the surviving item.
- Exclude review-process prose, comment-cleanup summaries, and other non-findings.
- Put findings already classified by the source review as `Improbable / Not Worth Handling` in `Source notes`, not the actionable queue. Reopen one only if the user explicitly asks.
- Record closely related findings in a group when they share a root cause, require one design decision, or must be implemented together. Do not group items merely because they touch the same file.
- Give each item a concrete default approach after read-only inspection of the relevant code. Write `needs discussion` when a sound plan requires a user decision.

Use this shape, omitting empty optional fields:

```markdown
# Review Todo

- State: triage
- Created: 2026-08-15T14:00:00+02:00
- Updated: 2026-08-15T14:00:00+02:00
- Next: 1

## Pre-existing worktree

- `M path/from-git-status`

## Groups

- G1: Short root-cause name — findings 2, 3

## Findings

### 1. Short finding title

- Severity: should-fix
- Location: `src/example.ts:42`
- Group: none
- Status: pending
- Source: code-review
- Finding: What is wrong and why it matters.
- Default approach: The concrete fix to use if the user says `fix 1`.
- Decision: —
- Implementation: —
- Commit: —

## Source notes

- Non-actionable review material worth preserving.

## Implementation groups

- Not planned yet.
```

Allowed finding statuses are `pending`, `planned`, `ignored`, `implementing`, and `implemented`. Allowed workflow states are `triage`, `implementing`, `blocked`, and `complete`.

Write the file before presenting the first issue. From then on, read it at the start of every turn and update `Next`, `Updated`, and the affected entries immediately after each decision or implementation result. Do not rely on the chat transcript as the only record.

### Step 3: Apply direct decisions

Interpret commands against stable IDs, including comma-separated IDs and ranges:

- `fix 2, 3` accepts each item's default approach and marks it `planned`.
- `ignore 7` marks it `ignored`. Record the user's reason; if none was given, record `Declined by user (no rationale given)` rather than inventing one.
- `fix` or `ignore` without IDs applies to the item or group currently being presented.
- `fix all remaining`, `ignore all remaining`, and `ignore all trivial` apply literally after showing the affected IDs.
- A user-supplied approach replaces the default approach and becomes the recorded decision.

For a group, keep individual statuses so the user can accept or reject members separately. If the same ID receives conflicting directives, an ID is unknown, or `fix` targets an item whose approach says `needs discussion`, apply the unambiguous directives and ask only about the ambiguous subset.

Users may revise a decision during triage. Update the existing entry; do not create a duplicate. Never edit production code while any finding remains `pending`.

### Step 4: Present undecided findings

Order pending work by:

1. severity: critical, should-fix, nice-to-have;
2. root causes before symptoms and prerequisite decisions before dependents;
3. original review order when otherwise equal.

Before presenting an item, inspect the current code to confirm its context and sharpen the plan. If the finding is stale, already fixed, or a false positive, explain the evidence and recommend ignoring it; the user still makes the disposition.

Present one issue or one coherent group at a time. Include:

- stable ID, severity, and location;
- the problem and impact in concise language;
- its relationship to other findings, if grouped;
- the recommended implementation approach and any tradeoff requiring a choice.

Ask whether to fix it with that approach, ignore it, or change the approach. After the answer, record the disposition and every material implementation constraint in `.review-todo.md` before moving on. End each triage response with a compact count such as `Review todo: 3 planned · 1 ignored · 4 pending`.

Treat a finding as trivial only when its fix is obvious, local, low-risk, and has no design tradeoff. Hold pending trivial items until all substantive findings are decided, then present them in one compact table with individual IDs and default approaches. Let the user accept or ignore the batch with per-ID overrides.

### Step 5: Finalize the implementation plan

When no finding remains `pending`:

1. Partition all `planned` findings into the fewest logical implementation groups. Put a fix with its tests, docs, generated output, and dependent findings in the same group. Split only changes that stand alone and can be committed independently.
2. Write the ordered groups, finding IDs, expected files, verification, and proposed `feat`, `fix`, or `chore` commit subject under `Implementation groups`.
3. Check the plan against every non-ignored finding. No planned ID may be absent.
4. Set the workflow state to `implementing` and begin immediately. Do not ask for another approval gate; triage decisions already authorize the work and commits.

If all findings were ignored, mark the workflow complete, summarize the decisions, remove `.review-todo.md`, and make no commit.

### Step 6: Implement, verify, and commit

Process implementation groups in dependency order:

1. Mark the group's findings `implementing` and make exactly the recorded changes. Preserve unrelated and pre-existing worktree edits.
2. If implementation reveals a materially different design choice, stop that group, set the workflow to `blocked`, record the evidence and new choice required, and return it to the user. Continue automatically after the decision is recorded.
3. Run verification proportional to the change. Add or update tests when the accepted finding requires them. Record commands and results in the affected findings.
4. Mark the findings `implemented` only after their verification passes.
5. Commit the group before starting an independent group. Follow the repository's commit policy:
   - Stage only files and hunks changed for this group; never use broad staging commands.
   - Never stage `.review-todo.md` or a pre-existing/user-owned hunk.
   - Preserve unrelated staged changes. If they cannot be excluded safely without disturbing the user's index, set the workflow to `blocked` and ask the user to clear or authorize index handling.
   - Inspect the staged diff before committing.
   - Use only `feat:`, `fix:`, or `chore:` with a short subject and no body by default.
   - Keep dependent code, tests, docs, and generated files in the same commit.
   - Never bypass hooks and never push.
6. Record the commit hash and subject in each included finding and in the implementation group.

When every planned finding is implemented and committed, set the workflow to `complete`. Verify that `.review-todo.md` is the only remaining workflow-owned uncommitted file, summarize planned fixes, ignored findings, verification, and commits, then remove the file. If other changes remain, identify them as pre-existing or user-owned and leave them untouched.

## Examples

### Example 1: Start with direct decisions

User invokes `review-todo fix 2, 3, 9; ignore 7` immediately after a review with ten findings.

Actions:

1. Create `.review-todo.md` with findings 1–10 and stable IDs.
2. Mark 2, 3, and 9 `planned` with their inspected default approaches; mark 7 `ignored`.
3. Present finding 1, or its coherent group, then continue through only 4, 5, 6, 8, and 10.
4. Batch any remaining trivial items at the end.
5. Once every item is planned or ignored, write the implementation groups, implement them, verify them, and commit each independent group.
6. Report the commits and remove `.review-todo.md`.

### Example 2: Discussion changes the approach

The current item is finding 4. The default approach replaces a public API, but the user says, `Fix 4, but keep the old method as a deprecated compatibility wrapper until the next major release.`

Record finding 4 as `planned`, replace its decision with that compatibility constraint, and include wrapper coverage in its verification plan. Present the next pending item. During implementation, keep the wrapper and its tests in the same commit as the new API.

### Example 3: Resume after context loss

The user invokes `review-todo resume` in a later turn. Read `.review-todo.md`, report the current counts and any blocked choice, then continue with `Next`. Do not reconstruct or renumber findings from memory.

## Troubleshooting

### No review is available

**Cause:** The skill was invoked without a completed review in context and no active state file exists.
**Solution:** Ask the user to paste the findings or run a review. Do not invent findings or create an empty state file.

### An active state file conflicts with a new review

**Cause:** A previous workflow did not finish.
**Solution:** Preserve the file and ask whether to resume it or replace it. Never merge two reviews or overwrite active decisions implicitly.

### A finding changed during implementation

**Cause:** Current code or a dependency makes the accepted approach unsafe or infeasible.
**Solution:** Record what was discovered, mark the workflow `blocked`, and ask only for the new material decision. Do not silently substitute a different design.

### A commit would include unrelated changes

**Cause:** A planned file already had user or another session's edits, or the index contains foreign changes.
**Solution:** Stage only workflow-owned hunks and inspect the staged diff. If ownership cannot be determined safely, leave the ambiguous hunk unstaged and ask the user rather than widening the commit.

### Verification or a commit hook fails

**Cause:** The implementation is incomplete, or a repository-wide check exposes a failure outside the changed scope.
**Solution:** Diagnose and fix failures caused by the implementation. Record genuine unrelated failures and keep the workflow `blocked` if they prevent a safe commit. Never weaken verification or bypass hooks.
