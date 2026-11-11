---
name: codebase-review
description: Review a whole codebase aspect by aspect, with aspects fitted to the project type (mobile, desktop, web frontend, static site, CLI, backend, library) — overview, docs truth-check, architecture, tests, security, the type's own foundations, feature deep dives, consistency, architecture roadmap — writing a doc per aspect and a verified findings ledger that doubles as the TODO. Plans first (recon, `blind-spots`, `review-plan`, one start gate), then runs independently. `--fix` hands settled findings through `crew` to named worker sessions in worktrees or sibling checkouts, integrated locally by fast-forward without pushing; major user-facing and risky changes wait for decision waves at the end. Reports user-facing and other changes. Use for "codebase review", "review the whole codebase", "onboard me to this repo", "deep dive this app", "audit the code base", "review and fix everything". Not for a diff or PR (code-review), a CLI release pass (release-review), or building a feature (longshot).
argument-hint: '[--fix] [--aspects a,b,…] [repo paths or focus] (blank resumes a programme)'
effort: high
---

# Codebase Review

Review a codebase one aspect at a time. Each aspect produces a doc that explains how it works
and a set of verified findings (bugs, improvements, tidy-ups, doc errors). The findings
accumulate in one ledger that serves as the user's TODO. With `--fix`, worker sessions fix the
settled findings while the review continues, and the lead integrates their branches locally.

**Preparation needs the user; the run is independent.** Until the start gate is approved, stay
read-only and wait for an answer to every question asked. Silence, a question tool returning,
a preselected recommendation and the original invocation are none of them answers.

This skill is the lead. Worker sessions run `crew join` and follow the `crew` skill; their
briefs carry this skill's rules.

References:
- `references/aspects.md`: the aspect catalog by project type, how to pick from it, its order
  and each aspect's questions
- `references/formats.md`: programme, ledger, prompts, briefs, decision waves, the final report
- `references/workers.md`: what a codebase review adds on top of `crew` (setup records, brief
  rules, integration checks, cleanup)

## Review grading

Use only these finding priorities, in descending order:

- **Critical Issues (Must Fix):** a verified path causes data loss, a security failure, a materially
  wrong operation, or makes a core workflow unusable without reasonable recovery.
- **Improvements (Should Fix):** an ordinary supported workflow demonstrably fails or repeatedly
  imposes substantial friction, or a concrete design defect creates meaningful maintenance cost.
- **Suggestions (Nice to Have):** a worthwhile improvement with small practical impact, including
  optional polish, local simplification, and rare recoverable edge cases.

Grade the demonstrated consequence, realistic reachability, and available recovery against project
priorities. A category, missing convention, hypothetical future problem, or confidence that a claim
is true does not set its priority. Do not assign automatic severity floors or ceilings. Keep
unverified claims in validation gaps, outside the graded finding count; distinguish suggestions
from defects. For plans, trace the consequence if implemented and state the assumptions.

Use the short labels **Must Fix**, **Should Fix**, and **Nice to Have** in summaries and ledgers.
Keep effort, verification status, user-facing change size, and tool/vendor diagnostic ratings
separate. When called by `code-review`, return its requested evidence and impact fields; the parent
owns scoring and final triage. Otherwise apply this rubric directly. Omit empty priority sections.

**Reach** goes on every bug: `common`, `plausible`, `rare` or `misuse` (corrupt data, hostile
input, API abuse), with the concrete trigger. It feeds the priority and the fix policy.

## Risk flags

A fix that does any of these is held for a decision wave, whatever its user-facing level:

- removes or narrows something users can do today, or contradicts a promise
- changes a persisted or wire format, or what existing saved data means
- adds public API, or changes what an existing API does
- changes interaction or a default behaviour (focus, keys, clicks, timing)
- adds a dependency, a resource bundle or a packaging change
- adds global or shared mutable state
- adds an abstraction with one user
- is much larger than the failure it removes

Reviewers and verifiers put the flags on the entry. Workers check again while implementing,
where most flags appear, and stop a fix that trips an unlisted one. When the code and a promise
disagree, the user decides which is wrong: calling it a bug does not lift the first flag, and no
fix rewrites a promise to fit.

## The contract

State it back at the start gate:

1. **Every question up front.** After the start gate there are no questions, except for the
   stops below and the decision waves at the end of a `--fix` run.
2. **Rulings, not stalls.** Every judgment call is decided and logged in `programme.md` as
   `R<n> — <decision> — <why> — <cost if wrong>`.
3. **Held, not asked.** Under `--fix`, a major user-facing or risk-flagged change is parked as
   `held` with its dependents. The run continues around it; the user decides held items in
   waves at the end, never mid-run.
4. **Milestone pings only.** One line per finished aspect or integrated batch.
5. **Local and unpushed.** Writes go to the work folder and, at the end, the harvest into the
   repo's docs. Under `--fix` they also go to the worker branches. Approval of the start gate
   authorises:
   - creating the planned worktrees and branches
   - the workers' commits on their branches
   - fast-forward integration of those branches into the integration branch
   - building the regrouped history on its own branch in Phase 8
   - deleting the work folder once Phase 8's conditions hold

   Nothing is pushed, and no repo outside the plan is touched.

**The stops:** an irreversible or destructive operation; a security-sensitive action; a side
effect beyond the contract (a push, a release, a non-fast-forward change to the integration
branch); or the framing turning out to be wrong about something load-bearing. Everything else
is a ruling.

## The work folder

Everything the run produces lives in `.codebase-review/` at the root of the lead's checkout. A
multi-repo run uses the primary repo. Its layout:

- `programme.md`
- `findings.md`, the ledger and TODO
- `docs/<aspect>.md`, one per aspect
- `briefs/` and `reports/`
- `run/`, for raw findings, verifications and check logs (`$RUN`)
- `report.md`

The folder is scratch, never committed: at the start gate, append `/.codebase-review/` to
`.git/info/exclude` (local, shared with worktrees; `.gitignore` stays untouched). Do not choose
another location or ask about it. Phase 8 harvests what is durable and deletes the folder.

## Phase 0 — Start or resume, then recon

Look for `.codebase-review/programme.md` at the repo root.

- **Found:** read `programme.md` and the ledger. Print **Now**, **Next** and the in-flight
  batches. Run `crew status`, read any report in `reports/` not yet integrated, and integrate
  it. Then continue from **Now** without re-asking framing questions. A programme on
  disk is not approval for new scope.
- **Not found:** run the recon.

Recon comes before any question. Read the instruction files (`AGENTS.md`, `CLAUDE.md`,
`README.md`), the docs tree and ADRs, the stack and build files, the test setup, the CI and
lint config, the git state of every candidate repo, and any sibling checkouts. Use at most 3 read-only `Explore` agents, one per repo.
Draft the **system overview** from this (the first Core aspect in `references/aspects.md`), so
the interview is concrete. In it:

- **Tag the project types** per repo or package, with the signals behind each tag
  (`Types: app/ → mobile app; packages/ui → library: UI component — signals: …`). The tags pick
  the catalog sections, so a wrong tag means a wrong plan.
- **List the promises:** what the README, docs, help text and examples say users can do ("Tab
  can be recorded"), each with its source.

## Phase 1 — The interrogation

Invoke `blind-spots` on the brief, carrying the recon forward, and run it to completion. These
questions are mandatory wherever they fall in its tree:

- **Repos:** which are reviewed, which are read-only reference, and (with `--fix`) which are
  writable.
- **End state for open findings:** where findings still open at the end will live. The options
  are a roadmap or TODO doc in the repo, the issue tracker, or the work folder until they are
  addressed (which delays its deletion). Without `--fix`, every finding is still open at the
  end, so this question settles where the TODO lives.
- **Types and aspects:** confirm the type tags in the first round. Then propose Core plus every
  section the tags match, deduplicated, and the feature units for deep dives (feature areas,
  pages, commands, endpoint groups or modules). Every aspect of a matched section is planned or
  goes under Skipped with a one-line reason. Add the project-specific aspects the catalog lacks.
- **Baseline:** the branch and commit to review. Uncommitted user edits are reviewed at their
  committed version and are never mentioned.
- **Promises:** confirm the recon's list and ask what else must never break.
- **Smoke list:** about five core workflows, and how this session drives them with real input:
  events through the OS or the shipped binary (an example app with posted clicks and keys, the
  CLI in a shell, a browser), never calls into the code.
- **With `--fix`:**
  - **How settled the project is.** Ask it first: it sets the fix policy's default and the
    change budget (source-line growth over the baseline, tests and docs excluded):

    | Maturity | Default fix policy | Budget |
    |---|---|---|
    | Settled ("done", maintenance only) | bugs with a `common` or `plausible` reach, and doc errors; everything else to the TODO | 5% |
    | Active | the above, plus improvements of half a day or less and tidy-ups in code a fix already touches | 15% |
    | Overhaul | bugs, tidy-ups and doc errors; improvements of half a day or less | none |

    Under Settled and Active, `rare` and `misuse` bugs go to the TODO.
  - The **fix policy** per class, starting from that default.
  - What counts as a **major user-facing change** for this project. Major and risk-flagged
    changes are held. Minor ones are fixed and reported.
  - The **integration branch** and its checkout, normally the lead's own.
  - **Workers:** how many (propose from the codebase size), each in a new worktree or an
    existing sibling clone.
  - The **check command** per repo, and the commit convention.
- **Definition of done:** what the user must have at the end.

Answer the user's own opening questions with analysis in the first round. Do not hand them back.

## Phase 2 — The plan

Draft `programme.md` (format in `references/formats.md`) in the conversation: the framing, the
type tags, the aspect list in catalog tier order, and the Skipped list. Each aspect gets scope
paths, doc path, the sibling docs it builds on, its boundary with neighbours, the model, and
which aspects run in parallel (disjoint scopes only, at most 3). Scope paths also tell the
readiness analysis when an area is settled.

**Self-review the draft** for overlapping scopes, aspects without questions, aspects the
definition of done does not need (move them to Skipped) and missing framing. Then always run
`review-plan` and fold in its findings; bring any rejected one to the gate with the reason.

**Run the smoke list on the baseline** with real input. A failing check is the review's first
finding. A check that could not be driven records what was tried; "needs a device" without an
attempt is not a result.

## Phase 3 — Worker setup (`--fix` only)

Load `crew` and follow "Setup" in `references/workers.md`: propose each worker's home, create the worktrees on the user's yes, give the `crew join` line
for each session, and wait until every worker reports a green baseline and `crew status` shows
it joined and level. Without worker sessions, the ruled-fix findings go to `longshot` at the
end, with the ledger as its brief.

### Start gate

Present the framing (including promises, maturity, fix policy and budget), the type tags, the
baseline smoke results, the aspect plan with Skipped, the Workers table and the contract. Then
ask: **"Start the review with this plan? After you approve, you can leave it running."** Wait
for an explicit yes. A reply that changes scope gets settled and a revised gate.

After the yes, announce **"The review is starting. I'll decide details myself, hold major
user-facing changes for the end, and send milestone pings."** Only now create the work folder
and add it to `.git/info/exclude`. Confirm with `git check-ignore .codebase-review` that it is
excluded. Then write `programme.md`, recording the base commit, the user's approval message and
the baseline size (source, test and README lines, with the command that counted them).
Set `RUN` to the absolute path of `.codebase-review/run`.

## Phase 4 — The review loop

For each aspect, in plan order, with up to 3 in parallel where the plan allows:

1. **Review.** Dispatch the aspect reviewer (prompt in `references/formats.md`). It writes the
   doc and `$RUN/findings-<aspect>.md`, and returns a 15-line summary.
2. **Verify.** A fresh verifier re-checks each finding at its `path:line`, fixes the line
   numbers, rejects what the code disproves, and marks duplicates of existing ledger entries.
   A finding with no verification mark never gets handed off.
3. **Second opinion, where it pays.** Invoke `second-opinion` for any of the following:
   - a potentially consequential finding the verifier only rated `✔ (likely)`; keep it ungraded until confirmed
   - a security or data-loss finding
   - a recommendation that would restructure a whole area

   Give it the finding and the code, not your conclusion. Use at most one call per aspect.
   Record disagreements on the entry.
4. **Ledger.** Merge the verified findings into `findings.md` under the aspect's section, with
   stable IDs. Under `--fix`, rule each one against the fix policy and its Reach: `fix`, `todo`
   or `held`. Any risk flag means `held`. Mark the dependents of held entries as blocked.
5. **Docs.** A wrong repo doc is a `D` finding; a missing one is an improvement; a promise the
   code breaks is held, never a `D`. **The docs rule** binds every doc change in the run: fix
   what is wrong, add only what that doc's readers need, and keep internals (private names,
   wire formats nobody writes by hand) out of README and agent files.
6. **Ping**, for example `Aspect 7/22 done — auth: 19 findings (6 bugs), 2 held. On to analytics.`
   Send it in the same message as the next dispatch. An ended turn is a stopped run.

**An anomaly is a finding until disproved.** Unexpected behaviour in a probe, test or
reproduction goes in the ledger as `✔ (likely)`, even when it looks like an artefact. Only a
real-input reproduction dismisses it.

**Context discipline is what lets this finish.** Raw findings, verifications and logs stay in
`$RUN`. This session reads the counts and the 15-line summaries, and pulls an entry in only to
rule on it. A run that reads reports inline compacts every few aspects.

## Phase 5 — Hand-off while reviewing (`--fix` only)

After each aspect is verified, run the readiness analysis. A finding is **ready** when all of
the following hold:

- it is verified, ruled `fix`, and not held
- everything in its Depends list is fixed or decided
- **its area is settled:** no queued or running aspect has a scope that covers its files
- its Touches do not overlap a batch in flight
- it is not a multi-area refactor; those wait until Phase 6 has named the theme they belong to

Group ready findings into batches of 3 to 8 in one area, write `briefs/B-n.md`, and deliver it
to an idle worker per crew's "Lead: the loop". Do not monitor it. On its report, integrate with
crew plus the additions in `references/workers.md`, running the check yourself, then return to
the review. Prioritise batches that remove code; hand-offs usually begin during tier 3.

**Bigger changes go through `plan` or `longshot`.** A finding or theme that spans areas,
changes a shared interface, or costs more than about half a day goes alone in its brief, marked
`Approach: plan` (or `longshot` for multi-hour work).

**Track the change budget.** After each integration, recount source lines as the baseline was
counted. Past the budget, bugs still go out, but every improvement and tidy-up not yet handed
off is held as one wave item: fix them anyway, or move them to the TODO?

## Phase 6 — Synthesis

Run the synthesis aspects from `references/aspects.md` once every planned aspect is verified:

1. **Consistency sweep** with `review-consistency`, over the competing patterns the aspects
   found.
2. **Consolidation:** docs consistency and findings staleness at the current HEAD, as two
   parallel agents. Under `--fix`, integrated batches have moved the code, so this pass also
   retires findings that a fix resolved in passing.
3. **Hotspots:** churn × size × fix commits.
4. **Architecture and roadmap.** Use an `opus` agent with `review-architecture` as the lens. It
   writes `architecture.md` and the Priorities section at the top of the ledger, and names the
   cross-cutting themes. Check the roadmap with `second-opinion`.

Under `--fix`, multi-area refactors now become batches or held items, according to the
themes and the fix policy.

## Phase 7 — Decision waves (`--fix` only)

Start once the review is complete and every ready batch has been handed off and integrated.

**Keep audit first**, because a fix that made the code worse looks just like one that made it
better. Split `<base>..HEAD` by area into at most 4 slices, each for a fresh `opus` agent with
the keep-audit prompt (`references/formats.md`), which never sees the rulings. It rates each
change `real fix`, `worthwhile`, `churn` or `worse` and lists behaviour changes no finding asked
for. Each `churn`, `worse` or unasked-for change becomes a keep-or-drop wave item; a drop is
reverted by a worker, and the Phase 8 regroup folds the revert away.

Then present the held items in waves (format in `references/formats.md`): each a scenario in
the user's terms with options and a recommendation, the most-unblocking first, each wave only
mutually independent decisions. Record answers as `decided wave <n>`, re-run readiness, and
present the next wave while the new batches run. Stop when nothing is held or the user parks
the rest as TODO.

## Phase 8 — Final checks, harvest, regroup and report

Under `--fix`:

1. Run the check command on the integration branch yourself.
2. Run `code-review` over `<base>..HEAD` of the integration branch, with `--multi` when more
   than about 30 commits landed. Send the fixes to a worker as a final batch, then re-review
   only those fixes.
3. **Run the smoke list with real input**, after any drops, then `qa` over the user-facing
   changes. A check that did not run, with what was tried, goes first under Blocked on you,
   and the report does not call the run complete.
4. Run `doc --update` over the integrated range, under the docs rule, so the repo docs reflect
   what the fixes changed.

### Harvest

**Harvest with `doc`**, under the docs rule, whatever the repo's next reader needs and lacks:

- how the system works, where the repo lacks it: architecture, data flow, startup, state
  ownership
- the conventions the consistency sweep settled
- decisions from the waves that constrain future work, as ADRs if the repo keeps them
- the promises and the smoke list, in the agent instructions file (`AGENTS.md` or
  `CLAUDE.md`), so the next agent neither narrows a promise nor skips the check
- the roadmap

Leave behind the review mechanics (IDs, marks, batches, run rulings) and anything the code now
says. Under `--fix`, commit the harvest on the integration branch; otherwise leave it
uncommitted. **Move the open findings** to the end state the interview settled. For an issue
tracker, write the issue texts into the report; never create issues yourself.

### Regroup the history (`--fix` only)

Per-finding commits suit integration, not history: batch order, repairs apart from what they
repair, messages covering one finding. Rebuild `<base>..HEAD` as feature commits:

1. **Group** the commits by feature or user-visible change, reordering freely. Fold every
   repair, revert and review fix into the commit it changes; a change and its revert vanish
   together. Tests and docs go with their change, and each message covers its whole diff in
   the repo's convention.
2. **Build** it on `codebase-review/regrouped`, from the base, in a worktree: cherry-pick each
   group's commits with `-n` in order, resolving conflicts to the integration tip's version,
   then commit once per group.
3. **Verify** that `git diff <integration branch> codebase-review/regrouped` is empty and that
   the check command passes on the regrouped tip. A non-empty diff is a regroup bug: fix the
   regroup, never the code.

(`squash-commits` only merges neighbours, so it cannot.) Adopting it rewrites the integration
branch, so it waits for the user's yes to the report; then keep the old tip as
`codebase-review/full` and run `git reset --keep codebase-review/regrouped`.

### Report

Write the final report from the template in `references/formats.md` to
`.codebase-review/report.md` and print it in full, Blocked on you first. Do not remove worktrees
or delete branches.

### Delete the work folder

**Delete `.codebase-review/`** after checking that the ledger has no open entry, the harvest
commit or doc diff exists, and the report was printed here. If the end state is "the work
folder", or a check fails, keep it and say what holds it under Blocked on you; a later run
resumes and deletes it.

## Model per role

Pass `model` on every dispatch. An omitted model silently inherits the session's top tier.

| Role | Model |
|---|---|
| Recon (`Explore`) | `sonnet` |
| Aspect reviewer | `opus` for foundations, security, architecture and feature deep dives; `sonnet` for inventories (docs, dependencies, agent setup, tooling) |
| Verifier, consolidation | `sonnet` |
| Architecture and roadmap, keep audit | `opus` |

## Examples

### Example: onboarding to an inherited app, review only

User: *"I'm new on this app and middleware. Review it thoroughly: architecture, state, startup,
tests, everything. Don't commit anything."*

Actions: recon and overview; `blind-spots` settles the middleware as reference only, 22
aspects, and open findings staying in the work folder; `review-plan`, gate, yes; tiers 1–5 with
pings; synthesis; an architecture and a startup doc harvested into `docs/`, uncommitted.

Result: a report that leads with coverage and the roadmap, nothing committed, and the work folder
kept, because its 300 open findings are the user's TODO.

### Example: a library, review only

User: *"codebase-review this Swift package before I tag 1.0."*

Actions: recon tags it `library: UI component`; the plan takes Core, Library and UI component
library, with modules as feature units, so no client-app aspect is ever proposed. Skipped:
agent setup (no agent files).

Result: findings about accidental public API and an untested platform, and a roadmap toward 1.0.

### Example: review and fix with two workers

User: *"codebase-review --fix. Big repo. Hold anything that changes what users see in a major
way. I'll run workers."*

Actions:
1. Interview: Active, so a 15% budget; a flow or default change is major. The smoke list fails
   one check on the baseline, which becomes the first finding.
2. Setup: worktree `../app-cr-w1` and clone `../app2`, each running `crew join <lead>`. Gate, yes.
3. Hand-offs from tier 3. A worker stops one fix that would change the saved format; it is held.
4. The keep audit rates 3 changes as churn. Wave 1 has those 3 and 5 held items; two are dropped.
5. `code-review --multi`, the smoke list and `qa`, `doc --update`, harvest, regroup.

Result: 64 per-finding commits regrouped into 14 feature commits on a branch, with an identical
tree, adopted on the user's yes. All local, with 9 user-facing changes listed before → after
and source growth of 9%. The remaining TODO is ranked.

## Troubleshooting

### A finished project comes back with dozens of changes
**Cause:** the maturity question was skipped or answered Overhaul, or `rare` and `misuse`
findings were ruled fix.
**Solution:** re-ask the maturity question, re-rule the open findings against its default,
and let the keep audit put what already landed to the user as keep or drop.

### A core workflow breaks, but every test passes
**Cause:** recording, clicking or typing was only ever checked through unit tests and
in-process probes.
**Solution:** run the smoke list with real input. Turn the failure into a finding with a test,
and add the check to the smoke list if it was missing.

### A worker's branch won't fast-forward
**Cause:** another batch landed after the worker rebased, or the worker branched from a stale
tip.
**Solution:** `crew integrate` exits 3; message the worker to run `crew sync --rebase` and
re-report. Never merge with a merge commit, and never rebase on the worker's behalf. If it exits
4 (the user's uncommitted edits), record it in Blocked on you and carry on.

### A worker reports green, but the check fails on the integration branch
**Cause:** tests were deselected, an exit code was swallowed by a pipe, or the worker did not
rebase.
**Solution:** the lead's own check run is the verdict. Send the log path back as a new batch.
Never rewind the integration branch without the user.

### Context runs out mid-run
**Solution:** re-read `.codebase-review/programme.md` (Now, Start, Workers, Batches) and the ledger, then resume.
If no start approval is recorded, ask before continuing; never invent one.
