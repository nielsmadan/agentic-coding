---
name: research
description: Research non-programming topics online from multiple sources. Use when asking about life decisions, consumer purchases, freelancing, finance, career strategy, travel, regulations, marketing, health, or any general knowledge question. Also handles programming-adjacent topics like marketing a dev blog or freelancer career strategy. Triggers on "research", "find out about", "what are my options for", "how to handle", "best way to", comparisons like "X vs Y" for non-technical topics, or questions about real-world products, services, and strategies. Do NOT use for programming, library docs, or code debugging — use research-online instead.
argument-hint: <topic or question>
---

# Research

Research any non-programming topic from multiple angles using web searches, with critical evaluation of source credibility.

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
- Regional questions need regional sources. A US-centric answer about investments is useless for a question about Germany. Verify locale in the synthesis.
- Quick mode may miss nuance. If a seemingly simple question turns out complex (e.g., "best savings account" depends on amount, duration, tax status), note this and suggest re-running in Standard mode.

## Workflow

### Step 1: Check Existing Knowledge

Before searching, assess whether you can already answer this well from training data:
- **If high confidence** (well-established facts, stable domain, no need for current data): answer directly, note you didn't search, and offer to research if the user wants verification or more depth.
- **If medium confidence** (you have a good answer but it may be outdated, incomplete, or regionally wrong): do a focused search (Quick mode) to verify and supplement.
- **If low confidence** (unfamiliar topic, rapidly changing domain, need current prices/regulations/options): proceed with full research.

This avoids 15 searches for a question like "pros and cons of UG vs GmbH" that Claude can already answer well.

### Step 2: Parse Input

Extract from the user's query:
- **Topic** (e.g., "risk-free investments", "freelancer CV", "bed and mattress")
- **Region/locale** (if mentioned, e.g., "Germany", "EU", "Berlin")
- **Personal context** (if given, e.g., career stage, budget range, life situation)
- **Budget/constraints** (if mentioned, e.g., price range, timeline)
- **Comparison targets** (if comparing: "X vs Y", "X or Y")
- **Goal/intent** (what they're trying to decide, achieve, or understand)

### Step 3: Classify Query Depth

| Mode | When | Search budget | Behavior |
|------|------|---------------|----------|
| **Quick** | Simple factual lookup, single-answer questions, verification of existing knowledge | **3-4 searches** total | Run General + Authority searches only. Skip follow-up loop and critique. Straight to synthesis. |
| **Standard** | Comparisons, strategy/how-to, experience-based, regional, multi-factor decisions, consumer research | **8-12 searches** total | Full workflow including follow-up loop and adversarial critique. Stop when diminishing returns — if 3 searches return the same info, don't keep searching that angle. |

Query type classification (influences which searches to run):

| Query Type | Signals | Search groups |
|-----------|---------|---------------|
| **Simple factual** | "What is", "How much", "When does" | Quick: General + Authority |
| **Opinion/experience** | "How do you handle", "What's it like", "tips for" | General, Community |
| **Comparison** | "vs", "or", "compare", "which is better", "best X" | General, Comparison, Community |
| **Regional/localized** | Country/city mentioned, regulations, local services | General, Authority, Regional |
| **How-to/strategy** | "How to", "best way to", "strategy for" | General, Community, Authority |
| **Consumer/purchase** | Product names, "buy", "price", "worth it", "quality" | General, Comparison, Community, Regional |

When in doubt, use Standard.

### Step 4: Run Searches

Run the relevant searches sequentially. Each search group below is 1-3 `web_search` calls plus optional `web_fetch` calls for promising results. **Track your search count and stop at the budget limit.** If earlier searches already answered the question well, skip remaining groups.

| Search group | Run when | Purpose |
|-------------|----------|---------|
| **General** | Always | Broad web search for the topic |
| **Community** | Opinion/experience, comparison, consumer, strategy queries | Reddit threads, Quora, forums — candid experiences, warnings. For genuinely niche topics (specific hobbies, medical conditions, specialized professions), also search specialized forums beyond Reddit. |
| **Authority** | Factual, regulatory, financial, health queries | Government sites, established institutions, official sources |
| **Comparison** | Query contains "vs", "or", "compare", "which", "best" | Structured comparisons, pros/cons, rankings |
| **Regional** | Query mentions a country, city, or region-specific topic | Localized information, local regulations, region-specific options |
| **News** | Topic likely affected by recent events, policy changes, market shifts | Up-to-date reporting, recent developments |

**For Germany-specific queries:** Always include German-language searches. Key authoritative German sources: Finanztip (personal finance), Verbraucherzentrale (consumer protection), Stiftung Warentest (product testing), Check24 (price comparison), IHK (business/freelancing). Search in German — e.g., "Tagesgeld Vergleich 2026" rather than "savings account comparison Germany."

For full search prompt templates, see `references/agent-prompts.md`.

### Step 5: Deduplicate Results

Before evaluation, deduplicate: if multiple searches found the same URL, keep the richest entry. Note when independent searches converge on the same source — this increases confidence.

### Step 6: Critical Evaluation

Evaluate each source:

**Recency:**

| Age | Dynamic topics (finance, prices, regulations) | Stable topics (life skills, strategy, career) |
|-----|----------------------------------------------|-----------------------------------------------|
| < 1 year | High | High |
| 1-3 years | Medium | High |
| 3-5 years | Low | Medium |
| > 5 years | Very Low | Low |

**Authority:**

| Source Type | Score |
|-------------|-------|
| Government/official sites (.gov, EU institutions, central banks) | High |
| Established test/review institutions (Stiftung Warentest, Consumer Reports) | High |
| Major publications of record, recognized domain-specific sites (Finanztip, Verbraucherzentrale) | High |
| Professional associations, industry bodies | Medium-High |
| Recognized expert blogs, academic sources | Medium |
| Community platforms with high engagement (Reddit >100 upvotes) | Medium |
| General blog posts, content marketing articles | Low |
| Anonymous forums, low-engagement posts, SEO "Top 10" listicles | Very Low |

**When sources conflict:**
- Factual/regulatory topics: prefer official/government sources
- Experience/opinion topics: prefer breadth of experiences over single authoritative voice
- Note when official guidance and real-world experience diverge

### Step 7: Follow-Up Search Loop (Standard mode only)

If the core question remains unanswered or a key angle has no sources, run 1-2 targeted follow-up searches. **Max 1 follow-up cycle, max 2-3 additional searches.** If the gap persists, note it as low-confidence.

### Step 8: Adversarial Critique (Standard mode only)

Brief self-challenge before presenting:

- What would someone who disagrees say?
- Are we over-weighting one source type?
- Could "independent" sources trace back to the same original?
- **Is any source affiliate-driven or sponsored?**
- **Are we assuming a specific country/culture?** Verify regional applicability.
- **Is there survivorship bias?** (People who succeeded post more than those who failed.)

If the critique reveals a blind spot, adjust and lower the confidence level.

### Step 9: Present Results

**Lead with the answer, not the research process.** Keep the output concise — a tight answer with source backing is better than a report with empty sections.

Structure:
1. **Answer the question directly** — recommended approach, key findings with inline source counts (e.g., "(3 sources)" or "(1 source, low confidence)")
2. **Key references** — 2-3 most influential sources with URLs
3. **Additional detail only if it adds value** — comparisons, regional specifics, conflicts. Skip sections that are empty or would repeat the answer.

For the full output format template, see `references/output-format.md`.

## Examples

### Example 1: Career/Freelancing Strategy
```
/research How do freelancers handle too many projects for a CV?
```
Query type: How-to/strategy + Opinion/experience
Searches: General, Community (Reddit-focused)

### Example 2: Regional Finance
```
/research Options for risk-free investments in Germany
```
Query type: Regional + Factual
Searches: General, Authority, Regional (German-language: "sichere Geldanlage 2026", "Tagesgeld Vergleich"), Community

### Example 3: Marketing Strategy
```
/research How to promote a programming blog
```
Query type: How-to/strategy
Searches: General, Community, Authority

### Example 4: Consumer Research (Regional)
```
/research Price and quality tiers for beds and mattresses in Germany
```
Query type: Consumer/purchase + Regional
Searches: General, Comparison, Regional (German-language: "Matratze Test Stiftung Warentest"), Community

### Example 5: Comparison
```
/research freelancing vs full-time employment pros and cons EU
```
Searches: General, Comparison, Community, Regional

### Example 6: Quick Mode
```
/research What is the current deposit insurance limit in Germany?
```
Quick mode: General + Authority only (3-4 searches). Direct answer.

### Example 7: Skip Search (High Existing Knowledge)
```
/research What are the pros and cons of a UG vs GmbH?
```
Claude likely knows this well. Answer from training data, offer to search for verification or current details (e.g., minimum capital requirements may have changed).

## Troubleshooting

### No results found
Widen search terms — try alternative terminology, remove region constraint, or search for the underlying concept. For German topics, try both English and German queries.

### All sources are outdated
Flag explicitly in the synthesis with dates. Especially important for finance and regulatory topics.

### Sources conflict
Weight by authority type. Note the conflict with a resolution. Use inline source counts to make confidence transparent.

## Notes

- Track search count against budget (Quick: 3-4, Standard: 8-12) — stop at diminishing returns
- Always capture source metadata (URL, date, source type)
- Weight findings by credibility — a government source outweighs a random blog post
- For consumer research, be especially wary of affiliate content
- For Germany-specific queries, prefer German-language authoritative sources
- Use inline source counts "(N sources)" to make confidence transparent
