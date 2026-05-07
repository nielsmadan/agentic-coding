---
name: pre-existing
description: Fix any test/lint/type/build/CI failure instead of dismissing it as pre-existing, flaky, or unrelated. Triggers on red checks or `/pre-existing`.
argument-hint: "[optional: name of the failing check, file, or error]"
---

# Pre-Existing

**Don't investigate whether it's pre-existing. Just fix it.**

We don't care who broke it, when, or whether your changes caused it. The only acceptable end state is **all checks green**. Skip the forensics.

## When to invoke

Whenever you are about to:

- Call a failure "pre-existing", "already broken", "already failing", "was already there", or "not introduced by my changes"
- Call a test "flaky", "unrelated", "intermittent", or "environmental"
- Suggest the user "skip", "ignore", or "move on past" a test, lint, type, build, or CI failure
- Use `git diff` / `git blame` / `git stash` to argue a failure isn't your fault
- Stop a turn while any check is red

Also when the **user** types `/pre-existing`.

## What to do

1. **Reproduce.** Re-run the failing command. Capture the full output — exact error, file, line, stack trace.
2. **Read.** Open the failing file and the production code it exercises. Read every line of the error before diagnosing.
3. **Fix the root cause.** Edit the offending code. If the production code is correct and the check is stale (renamed symbol, outdated snapshot, old type), fix the test/lint/type expectation instead. If the failure is a tooling regression, update the dependency or config.
4. **Re-run the full suite.** Not just the one test — the whole failing command. Confirm green before stopping.

Do **not**:
- Run `git stash`, `git switch`, or any "is this my fault?" verification
- Add a skip / xfail / `// eslint-disable` / `# type: ignore` without explicit user OK
- Comment out the failing test or assertion
- Lower the strictness of the check
- Rebase/squash/force-push to make the failure disappear from the diff

## If you genuinely cannot fix it

Some failures are outside the current scope (e.g. an integration test that needs a network resource you don't have, or a fix that would require changes the user hasn't authorized).

1. State the root cause and what you tried.
2. Propose a concrete fix.
3. Ask the user whether to defer, suppress (with their approval of the exact suppression), or keep investigating.

The user — not you — makes that call.

## Escalation

After 2 failed fix attempts, invoke `/second-opinion`. After 4, invoke `/hard-fix`. Don't keep retrying the same approach.

## Examples

**typecheck error in a file you didn't touch.**
Wrong: "Pre-existing — my changes only touched `src/api/`." Stop.
Right: Read the error. Fix it. Re-run `tsc`. Green.

**A flaky-looking test.**
Wrong: "Flaky — unrelated to this PR."
Right: Read the test. Find the race / shared state / missing await. Fix it. If you can't, escalate to the user with what you checked.

**Lint warning in legacy code.**
Wrong: "Pre-existing in legacy code, ignoring."
Right: Read the warning. Fix it (usually three lines). If it's a stylistic rule that genuinely doesn't apply, ask the user before adding a scoped override.

## User-approved exceptions

If the user has explicitly told you in this session that a specific failure is OK to leave alone ("yeah, skip the e2e suite, staging is down"), honor it — and quote their words when you do. Do not infer permission from silence.
