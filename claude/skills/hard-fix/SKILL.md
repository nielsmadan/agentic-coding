---
name: hard-fix
description: Escalation workflow for stubborn bugs that persist after multiple fix attempts. Combines parallel investigation (research-online, debug-log, review-history, second-opinion), synthesizes findings, validates with second-opinion, and logs everything to docs/log for future reference. Use when a bug won't go away, you've tried several approaches, or you're stuck.
argument-hint: <description of the persistent problem>
---

# Hard Fix

Comprehensive investigation workflow for bugs that resist normal debugging.

## Usage

```
/hard-fix login keeps failing after auth changes
/hard-fix race condition in checkout - tried 3 fixes already
/hard-fix                              # Uses recent conversation context
```

## Workflow

### Phase 0: Pre-Check Past Issues

Before full investigation, check if we've solved this before:

```bash
grep -ri "<keywords>" docs/log/ 2>/dev/null | head -10
ls -la docs/log/ 2>/dev/null | grep -i "<related_terms>"
```

**If a matching past issue is found:**
1. Read the full log file
2. Present the previous solution to the user
3. Ask: "We encountered this before. Should I apply the previous solution, or run a fresh investigation?"

If no match or user wants fresh investigation, continue.

### Phase 1: Gather Context

Ask clarifying questions if needed:
- What behavior are you seeing vs. expecting?
- What fixes have already been tried?
- When did this start happening? (recent change, always broken, etc.)
- Are there error messages or logs?

Keep questions minimal - only ask what's essential.

### Phase 2: Parallel Investigation

Launch ALL of these simultaneously using the Task tool:

| Agent | Skill/Tool | Focus |
|-------|------------|-------|
| **Research** | `/research-online` | External solutions, known issues, library bugs |
| **Debug** | `/debug-log` | Add logging to trace the actual execution path |
| **History** | `/review-history` | Git blame, recent changes, past issue logs |
| **Opinion 1** | `/second-opinion` | Fresh perspective on the problem |

**Task prompts:**

**Research agent:**
```
/research-online {library_if_any} {error_or_symptom}

Focus on: known bugs, breaking changes, similar issues others faced
```

**Debug agent:**
```
/debug-log {problem_area}

Add comprehensive logging to trace the exact execution path and state
```

**History agent:**
```
/review-history {affected_files_or_area}

Look for: recent changes, when it last worked, who touched it, past similar issues
```

**Second opinion agent:**
```
/second-opinion

Problem: {description}
Tried: {list of attempted fixes}
Symptoms: {what's happening}

What are we missing?
```

### Phase 3: Collect and Synthesize

Wait for all agents. Combine findings into:

```markdown
## Investigation Summary

### What We Found

**From Research:**
{external findings - known issues, solutions, library bugs}

**From Debug Logs:**
{what the execution trace revealed}

**From History:**
{relevant changes, when it broke, past issues}

**From Second Opinion:**
{fresh perspectives, things we might have missed}

### Conflicts or Gaps
{where sources disagree or information is missing}

### Emerging Theory
{what the combined evidence suggests is the root cause}
```

### Phase 4: Validate with Second Opinion

Run `/second-opinion` again with the synthesis:

```
/second-opinion

We investigated a persistent bug. Here's what we found:

{summary from Phase 3}

Our current theory: {root cause hypothesis}
Proposed fix: {what we plan to try}

Does this make sense? What might we still be missing?
```

### Phase 5: Present Findings

Present to user:

```markdown
## Hard Fix Analysis: {problem}

### Root Cause (Confidence: High/Medium/Low)
{what we believe is causing this}

### Evidence
- Research: {key finding}
- Debug: {key finding}
- History: {key finding}
- Opinions: {consensus or disagreement}

### Recommended Fix
{specific steps to resolve}

### Alternative Approaches
{if main fix doesn't work}

### Validation Plan
{how to verify the fix worked}
```

Ask user: "Should I proceed with the recommended fix?"

### Phase 6: Log for Future Reference

After resolution (or even partial progress), write to docs/log:

**File:** `docs/log/YYYY-MM-DD-{IssueDescription}.md`

```markdown
# {Issue Title}

**Date:** {date}
**Status:** Resolved / Partially Resolved / Unresolved
**Affected Area:** {files/components}

## Problem
{description of the issue}

## Symptoms
{what was observed}

## Root Cause
{what was actually wrong}

## Solution
{what fixed it, with code snippets if relevant}

## Investigation Notes
{key findings from research, history, debug logs}

## Prevention
{how to avoid this in the future, if applicable}

## Related
{links to issues, PRs, or other log entries}
```

Create the docs/log directory if it doesn't exist:
```bash
mkdir -p docs/log
```

## Notes

- This is a heavyweight process - use for genuinely stuck problems
- The parallel investigation is key - each source provides different insights
- Always log the outcome, even if unresolved - future you will thank you
- Past issue logs are gold - check them first
