---
name: skill-review
description: Review an agent skill in this repo for quality and fix what the user approves. Combines a mechanical lint, a judgment pass against published skill-authoring best practices, evidence from the skill's real sessions, and live trigger and dry-run tests. Use when the user says "review this skill", "check skill quality", "audit skill X", "why does skill X keep failing", "improve skill X", or "lint the skills". Use --all for a lighter sweep of every skill. Not for writing a new skill (use skill-creator) or counting usage (use skill-usage).
argument-hint: "[skill-name | --all] [--no-live]"
---

# Skill Review

Find what makes a skill fail the agent that follows it, prove each finding with
evidence, and fix only what the user approves. Evidence from real use outranks
static opinion: a rule the agent broke in practice matters more than a style nit.

## Instructions

### 1. Resolve the target

A skill name selects one skill for a deep review. `--all` runs the sweep in step 7
instead. With neither, ask which skill.

Skills live in `loadout/skills/` (global), `loadout/kits/skills/` (kit)
and `.claude/skills/` (repo-local). Read the source, never a rendered copy under
`~/.claude/skills/` or another harness directory. Read SKILL.md and every supporting
file, then its history:

```bash
git log --follow --format='%h %ad %s' --date=short -- <skill-dir>
```

### 2. Lint

```bash
.claude/skills/skill-review/scripts/lint_skill.py <name>
```

It checks name and description limits, YAML validity, XML tags, body size, harness
invocation syntax, broken links, orphaned and nested files, script modes, and repo
wiring (publish classification, README row, Codex symlink). Each line carries a
severity; exit 1 means at least one error. Treat warnings as leads, not verdicts:
a `links` warning in a skill that generates docs may be a template for the target
project.

### 3. Judge against the rubric

Read [references/checklist.md](references/checklist.md) and review the skill
against sections 1-6. For the triggering section, compare the description with its
neighbours:

```bash
.claude/skills/skill-review/scripts/lint_skill.py --listing
```

Each finding needs the exact lines it concerns and the rubric source it rests on.
Report only problems a reader of the skill would act on; a list of every
conceivable improvement buries the few that matter.

### 4. Gather evidence from real use

```bash
python3 .claude/skills/skill-usage/scripts/skill_usage.py --skill <name> --days 90
```

Pick up to six sessions: newest first, user-invoked over model-invoked, and favour
sessions after the last substantive edit from step 1, since older failures may
already be fixed. Hand them to reader subagents, two or three sessions each, with
the **Session reader** prompt in [references/prompts.md](references/prompts.md).
Transcripts are large, so they stay in the readers' context, not yours.

If the user described a failure (a project path, a date, what went wrong), find
that session first with `check-agent-logs` and include it. When there are no
sessions in the window, say so and widen to `--days 0` once.

Before citing a reader's quote, check it against the transcript with `--read`;
readers can paraphrase while appearing to quote.

### 5. Test it live

Skip this step under `--no-live`, and say that you did.

- **Trigger test:** one subagent with the **Trigger test** prompt, fed the
  `--listing` output and 16-20 prompts you write first.
- **Dry runs:** two or three subagents with the **Dry run** prompt, each on a
  realistic request, preferably one taken from a session found in step 4. Write
  the expected behaviours before dispatching. Run for real only when the skill is
  read-only; everything else is a described run.

The dry runs surface ambiguity: every "I had to guess" in a report is a finding.
Before dispatching, tell the user how the work is divided (readers plus testers).

### 6. Report, then fix what is approved

Present one ranked list. For each finding:

- **Severity:** *breaks* (the skill fails or misleads), *degrades* (works with
  friction, or triggers poorly), *polish*.
- **Evidence:** lint output, a rubric item with its source, a session ref with the
  user's quoted words, or a test result.
- **Fix:** the concrete edit, quoting the old and new lines.

Lead with findings that have usage or test evidence. Close with the count of agents
run. Then ask which fixes to apply.

Apply only the approved fixes, in the source directory, changing nothing beyond
them; in a skill the user wrote, suggest wording rather than rewriting their
prose. Then verify:

```bash
.claude/skills/skill-review/scripts/lint_skill.py <name>
loadout sync --global && loadout check --global    # global skills; run project sync for kit skills
python3 publish/sync.py --check-manifest --check-sources
```

Re-run any dry run whose failure a fix addressed and confirm it now passes. Leave
committing to the user.

### 7. Sweep every skill (`--all`)

Run the lint with `--all`, then review the `--listing` output as a whole: overlapping
descriptions, missing boundaries between competing skills, and descriptions that
bury the use case past the first sentence. No session mining or live tests in this
mode. Report lint errors, then the listing problems, then name the three skills most
worth a deep review, weighing usage from `skill_usage.py --days 30` against how
many findings each has.

## Examples

### Review one skill after it misbehaved

User: "review qa-tour, it gave up on a screen it could easily have reached"

1. Read `loadout/skills/qa-tour/` and its git log. Lint: clean.
2. Rubric: the setup section never says what to do when a prerequisite is
   unavailable locally (3. Instructions, "no step that depends on a tool the
   skill never tells the agent how to get").
3. `skill_usage.py --skill qa-tour` lists seven sessions; a reader finds the
   session where the agent said it could not reach the screen without sending an
   email, and quotes the user's correction.
4. A dry run of "tour the new inbox screen" reports a guess at the same step.
5. Report: one *breaks* finding with session and test evidence, plus two
   *polish* items. The user approves the first; apply it, sync, re-run the dry run.

### Sweep before publishing

User: "lint the skills"

Run `lint_skill.py --all`, review the listing for overlaps, and report: two errors
(invalid YAML in one frontmatter, an XML tag in a description), one trigger overlap
between two research skills, and three skills worth a deep review.

## Troubleshooting

### `uv` is missing or cannot resolve PyYAML

**Cause:** the lint runs as a uv inline script so it can parse YAML strictly.
**Solution:** install uv, or run `uv run --with pyyaml python3 <script>` with network
access once to populate the cache.

### A session reader returns nothing useful

**Cause:** the session was automated, truncated, or the skill only loaded in passing.
**Solution:** check the trigger column from `skill_usage.py`; model-invoked loads from
another skill are often incidental. Pick the next user-invoked session.

### Dry runs pass but the user still reports failures

**Cause:** the failing situation depends on state the test request lacked (data,
an unavailable service, a mid-run change).
**Solution:** rebuild the request from the failing session's actual context and run
it again.
