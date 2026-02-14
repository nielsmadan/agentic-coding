---
name: review-plan
description: Multi-agent review of implementation plans. Use after creating a plan but before implementing, especially for complex or risky changes.
argument-hint: [path to plan file or use current plan context]
---

# Plan Review

Comprehensive review of implementation plans using parallel specialized agents.

## Usage

```
/review-plan                          # Review plan from current context
/review-plan path/to/plan.md          # Review specific plan file
```

## Workflow

### Step 1: Extract Plan and Check Internal Docs

Get the plan to review:
- If path provided, read the file
- Otherwise, use the plan from current conversation context
- Summarize: problem statement, proposed solution, key implementation steps

**Check internal documentation:**
Use Grep to search for relevant keywords in `docs/` and `*.md` files. Look for documented patterns, architectural guidelines, or gotchas related to the plan's area.

### Step 2: Determine Review Scope

Based on plan complexity, decide:
- **Simple** (single file, minor change): Skip research agent, 2 alternatives
- **Medium** (few files, new feature): All agents, 3 alternatives
- **Complex** (architectural, multi-system): All agents + research, 4 alternatives

**Do NOT shortcut this workflow:**
- "I already know the issues" -- External perspectives find blind spots you can't see
- "This will take too long" -- Parallel agents run simultaneously, the time cost is minimal

### Step 3: Spawn Review Agents in Parallel

**CRITICAL:** Launch agents in a SINGLE message with multiple tool calls.
Do NOT invoke one at a time. Do NOT stop after the first agent.

| Agent | Purpose | Tool |
|-------|---------|------|
| **External Opinions** | Get Gemini + Codex input | Skill: `second-opinion` |
| **Alternatives** | Propose 2-4 other solutions | Task: general-purpose |
| **Robustness** | Check for fragile patterns | Task: general-purpose |
| **Adversarial** | Maximally critical review | Task: general-purpose |
| **Research** | Relevant practices online | Skill: `research-online` |

See [references/agent-prompts.md](references/agent-prompts.md) for full prompt templates for each agent.

### Step 4: Synthesize Findings

Collect all agent results and synthesize:

```markdown
## Plan Review: {plan_name}

### External Opinions

**Gemini:** {summary}
**Codex:** {summary}
**Consensus:** {where they agree}
**Divergence:** {where they disagree}

### Alternative Approaches

| Approach | Key Advantage | Key Disadvantage |
|----------|---------------|------------------|
| Current plan | {pro} | {con} |
| Alt 1: {name} | {pro} | {con} |
| Alt 2: {name} | {pro} | {con} |

**Recommendation:** {stick with plan / consider alternative X / hybrid}

### Robustness Issues

**Critical (must fix):**
- {issue}: {fix}

**Warnings:**
- {issue}: {fix}

### Adversarial Findings

**Valid concerns:**
- {concern}: {how to address}

**Dismissed concerns:**
- {concern}: {why it's not a real issue}

### Research Insights
(if applicable)
- {relevant finding}

---

## Revised Plan Recommendations

{specific improvements to make based on all feedback}

### Changes to Make
1. {change 1}
2. {change 2}

### Questions to Resolve
- {unresolved question}
```

### Step 5: Update Plan

If significant issues found, offer to revise the plan incorporating the feedback.

## Notes

- Use the Skill tool for `second-opinion` and `research-online` - do not write slash commands directly
- External opinions provide model diversity (Gemini + Codex)
- The adversarial agent should be harsh - that's its job
- Robustness review catches patterns that "work in testing, fail in prod" - see [references/robustness-patterns.md](references/robustness-patterns.md) for examples
- Research agent finds relevant practices and known issues online
- Always synthesize all agent results into actionable improvements
