# Workers and local integration (`--fix`)

The sessions, branches, delivery, worker loop and integration all come from the `crew` skill.
Load it at Phase 3. This file adds only what a codebase review layers on top.

## Setup (Phase 3, before the start gate)

Run crew's "Lead: setup" from the lead's checkout, on the integration branch the interview
settled. Worker homes are a new worktree (`crew add w1 --new-worktree`, the default) or an
existing sibling clone (`crew add <name> <path>`). The user's yes to the setup proposal
authorises creating the worktrees and branches.

When `crew status` shows every worker joined and level, record each hello in `programme.md`
under Workers: name, harness, checkout, branch, baseline check result. The start gate presents
that table.

## Briefs

Briefs go to `.codebase-review/briefs/B-<n>.md` and reports come back to
`.codebase-review/reports/B-<n>.md`. Use crew's envelope with this skill's Rules and the
findings as Items (`references/formats.md`, briefs). The risk-flag tripwire rides in the Rules:
a worker whose diff trips a flag the entry does not carry, or that has grown well past the
failure it removes, discards that change and reports the flag with the simplest alternative.

## Lead-side integration additions

On top of crew's "Lead: the loop", step 4:

- **Touches and proportion.** In the `--dry-run` listing, each commit must stay inside its
  finding's Touches (plus its tests and docs) and be in proportion to the failure. Read the
  diff of any that is not, and of any that touches a flagged area. A commit that refactors,
  renames or redesigns beyond its finding, or trips an unreported risk flag, goes back to the
  worker to be split or stopped, and the lead holds the finding.
- **Check log** goes to `$RUN/check-B-<n>.log`.
- **Ledger.** Mark the findings `fixed` with their shas and the batch done. Mark a finding
  stopped on a risk flag `held`, with the flag. Recount the size for the change budget.
- **Refused by the user's edits** (exit 4): record the branch in Blocked on you with the
  command crew printed, and keep handing out work in other areas.

## Cleanup (Phase 8)

Remove nothing. List crew's teardown commands in the report for the user to run once they are
satisfied. Once the regroup is adopted, the worker branches are contained in
`codebase-review/full`, not in the integration branch, so `branch -d` refuses. Give the check
and the forced delete instead:
`git merge-base --is-ancestor crew/w1 codebase-review/full && git branch -D crew/w1`.
