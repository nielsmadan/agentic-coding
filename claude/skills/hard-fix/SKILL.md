---
name: hard-fix
description: Escalation workflow for stubborn bugs. Use when a bug persists after multiple fix attempts, you've tried several approaches, or you're stuck.
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

**Do NOT shortcut this workflow:**
- "I think I already know the fix" -- If you knew, you wouldn't need this skill
- "Let me just try one more thing first" -- You've already tried. Follow the systematic process
- "I only need one of these investigation methods" -- Parallel investigation is the point, run ALL agents

**Circuit Breaker Rule:**
If 3 sequential fix attempts have failed for the same issue:
1. STOP attempting more fixes
2. Document what was tried and why each failed
3. This signals a systemic/architectural issue, not a localized bug
4. Recommend architectural review rather than continuing to patch

## Workflow

### Phase 0: Pre-Check Internal Documentation

Before full investigation, check internal docs for known issues and gotchas:

**Check past issues:**
```bash
grep -ri "<keywords>" docs/log/ 2>/dev/null | head -10
ls -la docs/log/ 2>/dev/null | grep -i "<related_terms>"
```

**Check project documentation:**
```bash
grep -ri "<keywords>" docs/ *.md 2>/dev/null | head -10
```

Look for documented gotchas, known issues, or patterns related to the problem area.

**If a matching past issue is found:**
1. Read the full log file
2. Present the previous solution to the user
3. Ask: "We encountered this before. Should I apply the previous solution, or run a fresh investigation?"

**If relevant documentation is found:**
1. Read the relevant sections
2. Check if documented patterns/gotchas apply to this issue

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
| **Library Source** | Read library code | Undocumented behavior, actual implementation |
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

**Library source agent:**
```
Subagent type: general-purpose
Prompt:
---
Investigate the source code of libraries involved in this issue:

Problem: {description}
Libraries involved: {library_names}

1. Find the library source code:
   - node_modules/{library}/ for JS/TS
   - Look for .dart files in pub cache for Flutter
   - site-packages/{library}/ for Python
   - vendor/ or go modules for Go

2. Locate the relevant functions/classes being used

3. Read the actual implementation and look for:
   - Undocumented behavior or edge cases
   - Default values that might cause issues
   - Error handling that swallows errors
   - Race conditions or timing assumptions
   - Version-specific behavior

4. Check if our usage matches what the library expects

Return findings about how the library actually works vs how we're using it.
---
```

**Second opinion agent:**
```
/second-opinion

Problem: {description}
Tried: {list of attempted fixes}
Symptoms: {what's happening}

What are we missing?
```

### Phase 3: Synthesize Findings

Wait for all agents. Combine into a root cause theory with evidence.

**BAD synthesis (superficial):**
```
Root Cause: The API call is failing.
Evidence: Got a 500 error in the logs.
Fix: Add a try-catch.
```

**GOOD synthesis (investigative):**
```
Root Cause: Race condition between auth token refresh and API call.
Evidence:
- Debug logs: Token refresh starts at T+0, API call at T+50ms, refresh completes T+200ms
- History: Started after PR #234 moved token refresh to background
- Library source: axios doesn't queue requests during refresh by default
- Research: Known issue axios#4193, recommended fix is axios-auth-refresh
Fix: Add request queuing during token refresh using axios-auth-refresh interceptor.
```

The difference: superficial stops at symptoms, good traces to mechanism.

### Phase 4: Validate Theory

Run `/second-opinion` with your synthesis and proposed fix. Check for blind spots.

### Phase 5: Present to User

```markdown
## Hard Fix Analysis: {problem}

**Root Cause** (Confidence: High/Medium/Low): {mechanism, not symptom}

**Evidence**: {one key finding per source}

**Recommended Fix**: {specific steps}

**Alternatives**: {if main fix fails}

**Validation**: {how to verify}
```

Ask: "Should I proceed with the recommended fix?"

### Phase 6: Implement and Verify

1. Implement the recommended fix
2. Ask user to test/verify
3. **Wait for user confirmation** that the fix worked

**Do NOT proceed to logging until user confirms the fix is working.**

### Phase 7: Log for Future Reference (after user confirms fix)

**Only after user confirms fix works**, write to `docs/log/YYYY-MM-DD-{Issue}.md`:

```markdown
# {Issue Title}

**Date:** {date} | **Area:** {files/components}

## Problem & Symptoms
{what was happening}

## Root Cause
{what was actually wrong - the mechanism}

## Solution
{what fixed it, with code if relevant}

## Prevention
{how to avoid in future}
```

## Examples

**Token refresh bug after multiple failed fix attempts:**
> /hard-fix auth token refresh fails silently after 3 fix attempts

Launches parallel agents: research finds a known axios issue with token queuing, debug-log traces the refresh timing, history reveals the bug started after PR #234 moved refresh to background, and library source confirms axios doesn't queue requests during refresh. Synthesizes a root cause (race condition) with a concrete fix using axios-auth-refresh.

**Race condition traced to library update via git history:**
> /hard-fix race condition in order processing since last deploy

History agent pinpoints a dependency bump that changed default concurrency behavior. Debug logging captures the interleaved execution order, and library source inspection confirms the breaking change in the new version. Presents the version diff and a targeted fix to restore the previous behavior.

## Notes

- This is a heavyweight process - use for genuinely stuck problems
- The parallel investigation is key - each source provides different insights
- Only log confirmed fixes - don't log until user verifies it works
- Past issue logs are gold - check them first
