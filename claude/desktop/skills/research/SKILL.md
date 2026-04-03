---
name: research
description: Research non-programming topics online from multiple sources. Use when asking about life decisions, consumer purchases, freelancing, finance, career strategy, travel, regulations, marketing, health, or any general knowledge question. Also handles programming-adjacent topics like marketing a dev blog or freelancer career strategy. Triggers on "research", "find out about", "what are my options for", "how to handle", "best way to", comparisons like "X vs Y" for non-technical topics, or questions about real-world products, services, and strategies. Do NOT use for programming, library docs, or code debugging — use research-online instead.
argument-hint: <topic or question>
---

# Research

Research any non-programming topic from multiple angles using parallel sub-agents, with critical evaluation of source credibility.

## Usage

```
/research How do freelancers handle too many projects on a CV?
/research Options for risk-free investments in Germany
/research How to promote a programming blog
/research best mattress brands in Germany price comparison
/research freelancing vs full-time employment in the EU
```

## Gotchas
- Many consumer comparison sites are affiliate-driven. Weight independent sources (Stiftung Warentest, government sites) over "Top 10 Best X" listicles.
- Regional questions need regional sources. A US-centric answer about investments is useless for a question about Germany. The Regional agent handles this, but verify locale in the synthesis.
- Quick mode may miss nuance. If a seemingly simple question turns out complex (e.g., "best savings account" depends on amount, duration, tax status), note this and suggest re-running in Standard mode.

## Workflow

### Step 1: Parse Input

Extract from the user's query:
- **Topic** (e.g., "risk-free investments", "freelancer CV", "bed and mattress")
- **Region/locale** (if mentioned, e.g., "Germany", "EU", "Berlin")
- **Personal context** (if given, e.g., career stage, budget range, life situation)
- **Budget/constraints** (if mentioned, e.g., price range, timeline)
- **Comparison targets** (if comparing: "X vs Y", "X or Y")
- **Goal/intent** (what they're trying to decide, achieve, or understand)

### Step 2: Classify Query Depth

| Mode | When | Behavior |
|------|------|----------|
| **Quick** | Simple factual lookup, single-answer questions ("What is X?", "How much does Y cost?", "When does Z open?") | Spawn only General + Authority (max 2 agents). Skip follow-up loop and critique. Go straight to synthesis. |
| **Standard** | Comparisons, strategy/how-to, experience-based, regional, multi-factor decisions, consumer research | Full workflow including follow-up loop and adversarial critique |

Query type classification (influences which agents spawn):

| Query Type | Signals | Default Agents |
|-----------|---------|----------------|
| **Simple factual** | "What is", "How much", "When does" | Quick: General + Authority |
| **Opinion/experience** | "How do you handle", "What's it like", "tips for" | General, Reddit, Forum |
| **Comparison** | "vs", "or", "compare", "which is better", "best X" | General, Comparison, Reddit, Forum |
| **Regional/localized** | Country/city mentioned, regulations, legal, local services | General, Authority, Regional |
| **How-to/strategy** | "How to", "best way to", "strategy for", "approach to" | General, Reddit, Forum, Authority |
| **Consumer/purchase** | Product names, "buy", "price", "worth it", "quality" | General, Comparison, Reddit, Regional |

When in doubt, use Standard.

### Step 3: Determine Which Agents to Spawn

| Agent | Spawn When | Purpose |
|-------|-----------|---------|
| **General** | Always | Broad web search for the topic |
| **Reddit** | Opinion/experience, comparison, consumer, strategy queries | Candid personal experiences, warnings, real-world reports |
| **Authority** | Factual, regulatory, financial, health queries | Government sites, established institutions, official sources |
| **Forum/Community** | Experience-based, niche queries | Specialized communities, expert forums, Quora |
| **Comparison** | Query contains "vs", "or", "compare", "which", "best" | Structured comparisons, pros/cons, rankings |
| **Regional** | Query mentions a country, city, or region-specific topic | Localized information, local regulations, region-specific options |
| **News** | Topic likely affected by recent events, policy changes, market shifts | Up-to-date reporting, recent developments |

### Step 4: Spawn Agents in Parallel

Launch ALL relevant agents in a **single message** (parallel execution). Each agent uses `subagent_type: general-purpose`.

**Every agent must capture metadata for each source:** URL, date, and source type (government / publication / expert blog / forum / news).

For full agent prompt templates, see `references/agent-prompts.md`.

### Step 5: Collect and Deduplicate Results

Wait for all agents to complete. Before evaluation, deduplicate: if multiple agents found the same URL, keep the entry with the richest metadata and merge unique context. Note which agents independently found the same source — convergence increases confidence.

### Step 6: Critical Evaluation

Before synthesizing, evaluate each source:

**Recency:**

| Age | Dynamic topics (finance, prices, regulations, markets) | Stable topics (life skills, general strategy, career advice) |
|-----|------------------------------------------------------|-------------------------------------------------------------|
| < 1 year | High | High |
| 1-3 years | Medium | High |
| 3-5 years | Low | Medium |
| > 5 years | Very Low | Low |

**Authority:**

| Source Type | Score |
|-------------|-------|
| Government/official sites (.gov, EU institutions, central banks) | High |
| Established test/review institutions (Stiftung Warentest, Consumer Reports, Which?) | High |
| Major publications of record (established newspapers, trade journals) | High |
| Professional associations, industry bodies | Medium-High |
| Recognized expert blogs, academic sources | Medium |
| Well-known community platforms with high engagement (Reddit >100 upvotes, popular Quora) | Medium |
| General blog posts, content marketing articles | Low |
| Anonymous forums, low-engagement posts, SEO-optimized "Top 10" listicles | Very Low |

**Relevance:** Exact topic and region match = High. Same domain, different specifics = Medium. Tangentially related = Low.

**When sources conflict:**
- For factual/regulatory topics: prefer official/government sources
- For experience/opinion topics: prefer breadth of experiences over single authoritative voice
- Note when official guidance and real-world experience diverge

### Step 7: Follow-Up Search Loop (Standard mode only)

After evaluation, check if any topic area has **fewer than 2 sources** or the core question remains unanswered. If so:

1. Identify the gap
2. Generate 1-2 targeted delta queries — more specific terms, alternative terminology, or broader scope
3. Spawn 1-2 follow-up agents
4. Merge new results, deduplicate, re-evaluate

**Max 1 follow-up cycle.** If the gap persists, note it as a low-confidence area.

### Step 8: Adversarial Critique (Standard mode only)

Brief self-challenge before presenting:

- What would someone who disagrees with this conclusion say?
- Are we over-weighting one source type? (e.g., all Reddit opinions, no official sources)
- Could any "independent" sources trace back to the same original?
- **Is any source affiliate-driven or sponsored?** Consumer comparisons and "best of" lists are often affiliate content — flag this.
- **Are we assuming a specific country/culture?** Verify regional applicability.
- **Is there survivorship bias in experience reports?** (People who succeeded post more than those who failed.)
- Is the recommended approach the simplest option, or are we over-complicating?

If the critique reveals a blind spot, adjust the synthesis and lower the confidence level.

### Step 9: Present Results

**Lead with the synthesis, not the raw data.** The user wants the answer first, with supporting evidence.

For the full output format template, see `references/output-format.md`.

## Examples

### Example 1: Career/Freelancing Strategy
```
/research How do freelancers handle too many projects for a CV?
```
Query type: How-to/strategy + Opinion/experience
Spawns: General, Reddit, Forum

### Example 2: Regional Finance
```
/research Options for risk-free investments in Germany
```
Query type: Regional + Factual
Spawns: General, Authority, Regional, Reddit

### Example 3: Marketing Strategy
```
/research How to promote a programming blog
```
Query type: How-to/strategy
Spawns: General, Reddit, Forum, Authority

### Example 4: Consumer Research (Regional)
```
/research Price and quality tiers for beds and mattresses in Germany
```
Query type: Consumer/purchase + Regional
Spawns: General, Comparison, Reddit, Regional

### Example 5: Comparison
```
/research freelancing vs full-time employment pros and cons EU
```
Spawns: General, Comparison, Reddit, Forum, Regional

### Example 6: Quick Mode
```
/research What is the current deposit insurance limit in Germany?
```
Quick mode: Spawns General + Authority only. Returns direct answer.

## Troubleshooting

### Agent fails or times out
Continue with remaining agents. Note the gap in synthesis and which source types are missing.

### No results found
Widen search terms — try alternative terminology, remove region constraint, or search for the underlying concept rather than the specific question.

### All sources are outdated
Flag explicitly in the synthesis. Note the dates and recommend verifying against current sources. This is especially important for finance and regulatory topics.

### Sources conflict with each other
Weight by authority type: official sources for facts/regulations, breadth of experience for opinions. Note the conflict with a resolution explaining which to trust and why.

## Notes

- All agents run in parallel for speed
- Each agent should complete in under 60 seconds
- Always capture source metadata for critical evaluation
- Weight findings by credibility — a government source outweighs a random blog post
- For consumer research, be especially wary of affiliate content
- For regional questions, verify the sources actually cover the correct region
