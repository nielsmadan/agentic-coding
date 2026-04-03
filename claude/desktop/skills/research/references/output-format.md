# Output Format Template

Lead with the synthesis, then include only the supporting detail sections relevant to the query. Skip sections that would repeat the synthesis.

```markdown
## Research Results: {topic}

### Synthesis

**Goal:** {one-line summary of what the user is trying to achieve or understand}

**Recommended Approach:**
{what the research suggests, prioritizing authoritative and recent sources}

**Key Findings (weighted by credibility):**
- {finding from high-credibility source}
- {finding from high-credibility source}
- {finding from medium source, noting caveat if needed}

**Confidence:** {High/Medium/Low}
- Based on: {e.g., "3 high-credibility sources agree", "official government source confirms"}
- Caveats: {any outdated info, unresolved conflicts, gaps, regional limitations}

**Key References:**
1. [{title}]({url}) — {why this source matters, e.g., "official government guidance"}
2. [{title}]({url}) — {why this source matters, e.g., "Stiftung Warentest independent test"}
3. [{title}]({url}) — {why this source matters} (optional)

---

### Supporting Details

(Include only sections relevant to the query, and only findings not already covered in the synthesis)

#### Official/Authoritative Sources
(factual/regulatory queries)
{government, institutional, or professional body findings}

#### Community Experience
(opinion/experience queries)
{Reddit threads, forum posts, personal accounts — with engagement context}

#### Comparison
(comparison queries only)

**{Option A}:**
- Pros: {list}
- Cons: {list}
- Best for: {use cases}
- Price range: {if applicable}

**{Option B}:**
- Pros: {list}
- Cons: {list}
- Best for: {use cases}
- Price range: {if applicable}

#### Regional Specifics
(regional queries only)
{local regulations, availability, pricing, cultural context}

#### Recent Developments
(if news agents found relevant updates)
{policy changes, market shifts, new options}

#### Conflicts
(only if sources disagree on something material)
- {source A} says X, but {source B} says Y
- **Resolution:** {which to trust and why}
```
