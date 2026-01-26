---
name: plan-review
description: Rigorous multi-agent review of implementation plans before execution. Spawns parallel agents for external opinions (Gemini/Codex), alternative solutions, robustness analysis, and adversarial critique. Use after creating a plan but before implementing, especially for complex or risky changes.
argument-hint: [path to plan file or use current plan context]
---

# Plan Review

Comprehensive review of implementation plans using parallel specialized agents.

## Usage

```
/plan-review                          # Review plan from current context
/plan-review path/to/plan.md          # Review specific plan file
```

## Workflow

### Step 1: Extract Plan

Get the plan to review:
- If path provided, read the file
- Otherwise, use the plan from current conversation context
- Summarize: problem statement, proposed solution, key implementation steps

### Step 2: Determine Review Scope

Based on plan complexity, decide:
- **Simple** (single file, minor change): Skip research, 2 alternatives
- **Medium** (few files, new feature): All agents, 3 alternatives
- **Complex** (architectural, multi-system): All agents + research, 4 alternatives

### Step 3: Spawn Review Agents in Parallel

Launch ALL relevant agents simultaneously:

| Agent | Purpose | Always Run |
|-------|---------|------------|
| **External Opinions** | Gemini + Codex via `/second-opinion` | Yes |
| **Alternatives** | Propose 2-4 other solutions | Yes |
| **Robustness** | Check for fragile patterns | Yes |
| **Adversarial** | Maximally critical review | Yes |
| **Research** | `/research-online` for relevant info | If warranted |

#### External Opinions Agent
```
/second-opinion

Review this implementation plan:

{plan_summary}

Key questions:
1. Is this the right approach?
2. What are we missing?
3. Any red flags?
```

#### Alternatives Agent
```
Subagent type: general-purpose
Prompt:
---
Given this problem and proposed solution:

**Problem:** {problem_statement}
**Proposed Solution:** {solution_summary}

Propose {2-4} alternative approaches. For each:

## Alternative {N}: {Name}

**Approach:** {brief description}

**Pros:**
- {advantage 1}
- {advantage 2}

**Cons:**
- {disadvantage 1}
- {disadvantage 2}

**When to prefer:** {scenarios where this is better}

Focus on meaningfully different approaches, not minor variations.
---
```

#### Robustness Agent
```
Subagent type: general-purpose
Prompt:
---
Review this plan for robustness issues:

{full_plan}

Check for these anti-patterns:

## Timing-Based "Solutions" (RED FLAGS)
- Timeouts to "fix" race conditions (use proper synchronization)
- Sleep/delay to wait for async operations (use await/callbacks/events)
- Polling when events/subscriptions are available
- Arbitrary delays hoping state settles

## Error Handling Issues
- Swallowing errors silently
- Catch-all without specific handling
- Missing rollback/cleanup on failure
- No retry strategy for transient failures

## State Management Issues
- Global mutable state without synchronization
- Optimistic updates without conflict resolution
- Cache invalidation assumptions
- Stale closure captures

## Concurrency Issues
- Shared state without locks/atomics
- Missing transaction boundaries
- Fire-and-forget async without error handling
- Assumption of execution order

## Scalability Issues
- O(n²) or worse algorithms on unbounded data
- Loading all data into memory
- No pagination/streaming for large datasets
- Blocking operations in event loops

For each issue found:
1. Quote the problematic part of the plan
2. Explain why it's fragile
3. Suggest a robust alternative
---
```

#### Adversarial Agent
```
Subagent type: general-purpose
Prompt:
---
Be maximally critical of this plan. Your job is to find flaws.

{full_plan}

Attack from every angle:

**Correctness:** Will this actually solve the problem? Edge cases?

**Completeness:** What's missing? What will break?

**Complexity:** Is this overengineered? Underengineered?

**Maintainability:** Will future developers understand this? Will it rot?

**Testing:** How will we know it works? What's hard to test?

**Deployment:** What could go wrong in production?

**Dependencies:** Are we relying on something fragile?

**Assumptions:** What are we assuming that might not be true?

Be harsh. Better to find problems now than after implementation.
Do not soften criticism. If something is bad, say it's bad.
---
```

#### Research Agent (if warranted)
```
/research-online {library/technology mentioned} {core problem}

Focus on:
- Known issues with proposed approach
- Best practices we might be missing
- Recent changes that affect the plan
```

Trigger research when:
- Plan involves unfamiliar library/API
- Implementing a pattern that might have established best practices
- Error messages or specific symptoms mentioned

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

## Robustness Anti-Pattern Examples

### Timing Hacks (Never Do This)

```javascript
// BAD: Timeout to "fix" race condition
await saveData();
await new Promise(r => setTimeout(r, 100)); // Hope it's done!
const data = await loadData();

// GOOD: Proper synchronization
await saveData();
await waitForSync(); // Explicit sync point
const data = await loadData();
```

```javascript
// BAD: Polling for state change
let ready = false;
while (!ready) {
  await sleep(100);
  ready = checkIfReady();
}

// GOOD: Event-based
await new Promise(resolve => {
  emitter.once('ready', resolve);
});
```

### Silent Failures

```python
# BAD: Swallowing errors
try:
    result = risky_operation()
except:
    pass  # Hope it worked!

# GOOD: Handle or propagate
try:
    result = risky_operation()
except SpecificError as e:
    logger.error(f"Operation failed: {e}")
    raise OperationFailedError(e) from e
```

### State Assumptions

```typescript
// BAD: Assuming state is current
const user = cache.get(userId);
user.balance += amount;  // Stale!

// GOOD: Optimistic locking or transactions
const user = await db.transaction(async (tx) => {
  const u = await tx.users.findUnique({ where: { id: userId } });
  return tx.users.update({
    where: { id: userId, version: u.version },
    data: { balance: u.balance + amount, version: { increment: 1 } }
  });
});
```

## Notes

- All review agents run in parallel for speed
- External opinions via `/second-opinion` provide model diversity
- The adversarial agent should be harsh - that's its job
- Robustness review catches patterns that "work in testing, fail in prod"
- Always synthesize into actionable improvements
