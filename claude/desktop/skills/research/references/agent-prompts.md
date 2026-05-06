# Search Prompt Templates

Templates for each search group. For each source found, capture: URL, date, and source type. Track your total search count against the budget (Quick: 3-4, Standard: 8-12).

## Encyclopedic Searches (Wikipedia)

**Run when:** Topic is unfamiliar OR you need a citation trail to primary sources (1 search, optional fetch)

```
Look up the topic on Wikipedia for grounding and citation trails.

web_search: site:en.wikipedia.org {topic}

If a relevant article exists, web_fetch the top 1-2 articles. Note:
- Which key claims have inline citations and what those cited sources are (these are leads for Authority / Community / Regional searches)
- Any Wikipedia dispute markers ([citation needed], NPOV warnings, "this article has multiple issues")
- Last revision date

Capture for each article:
- URL
- Last revision date
- Whether it has dispute markers
- Key cited sources for the main claims (URL + author/publisher)

Treat Wikipedia as **grounding, not authority** — follow its citations to the primary source rather than citing Wikipedia itself for load-bearing claims.

Skip Encyclopedic for: topics Claude already knows well at high confidence (the existing-knowledge check should have caught these), or for hyper-current topics where Wikipedia hasn't caught up.
```

## General Searches

**Run when:** Always (1-2 searches)

```
Search for information and guides on this topic.

web_search: {query_terms}
Optional: web_search: how to {goal_or_intent}

Focus on:
- Informative articles and guides
- Expert opinions and recommendations
- Practical advice and actionable steps

For each source, note:
- Source URL
- Publication date
- Source type: blog / guide / publication / news
- Author credibility if apparent

web_fetch the 1-2 most promising results for detail.
```

## Community Searches (Reddit + Forums)

**Run when:** Opinion/experience, comparison, consumer, or strategy queries (2-3 searches)

```
Search Reddit and community sources for real-world experiences.

web_search: site:reddit.com {keywords}
Optional for niche topics: web_search: {topic} forum experience
Optional for niche topics: web_search: site:quora.com {keywords}

Only search beyond Reddit for genuinely niche topics (specific hobbies, medical conditions, specialized professions). For most topics, Reddit alone covers the community angle.

Focus on:
- Real-world experience reports
- Warnings and gotchas not in official sources
- Candid opinions on trade-offs
- Product/service recommendations with reasoning

web_fetch the top 1-2 relevant threads. Focus on highly-upvoted comments.

For each source, note:
- URL and date
- Engagement level (upvotes, comment count)
- Authority: >50 upvotes = Medium, <10 upvotes = Very Low
```

## Authority Searches

**Run when:** Factual, regulatory, financial, or health queries (1-2 searches)

```
Search for authoritative and official sources.

web_search: {topic} site:gov.de OR site:europa.eu (adjust domains to region)
web_search: {topic} {established_institution} (e.g., Stiftung Warentest, BaFin, Verbraucherzentrale)

For Germany-specific queries, use German search terms:
- Finance: "Tagesgeld Vergleich", "sichere Geldanlage", site:finanztip.de, site:verbraucherzentrale.de
- Business: site:ihk.de, "Gewerbeanmeldung", "Freiberufler vs Gewerbe"
- Consumer: site:test.de (Stiftung Warentest), site:check24.de

Focus on:
- Government websites and official publications
- Established consumer testing organizations
- Central bank or financial authority guidance

For each source, note:
- URL, date, institution name
- Source type: government / institution / professional body
```

## Comparison Searches

**Run when:** Query contains "vs", "or", "compare", "which", "best" (1-2 searches)

```
Search for comparisons between the options mentioned.

web_search: {option_A} vs {option_B} {context}
Optional: web_search: best {category} {criteria} {current_year}

IMPORTANT: Flag affiliate content. Note if a source uses affiliate links or is a "best X" listicle site.

For Germany-specific comparisons, include German searches:
- web_search: {option_A} vs {option_B} Vergleich

Focus on:
- Direct comparison articles and independent test results
- Pros/cons and price/quality breakdowns
- Use case recommendations

For each source, note:
- URL, date
- Whether independent or affiliate-driven
```

## Regional Searches

**Run when:** Query mentions a country, city, or region-specific topic (1-2 searches)

```
Search for region-specific information.

web_search: {topic} {country/region}

For German topics, ALWAYS search in German — results are significantly better:
- web_search: {topic_in_german} {region}
- Key sites: finanztip.de, verbraucherzentrale.de, test.de, check24.de, ihk.de

Examples of German search terms:
- Investments: "Tagesgeld Vergleich 2026", "Festgeld beste Zinsen"
- Consumer: "Matratze Test 2026", "Bett kaufen Ratgeber"
- Freelancing: "Freiberufler Steuern", "Kleinunternehmerregelung"
- Real estate: "Mietpreisspiegel Berlin", "Wohnung kaufen Nebenkosten"

Focus on:
- Local regulations and legal requirements
- Region-specific options and pricing
- Local institutions and resources

Flag if a source covers a different region than requested.
```

## News Searches

**Run when:** Topic affected by recent events, policy changes, or market shifts (1 search)

```
Search for recent developments.

web_search: {topic} {current_year}

Focus on:
- Policy or regulatory changes
- Market shifts or price changes
- New options recently available

Only include genuinely recent results (within last 12 months). Don't pad with older news.
```

## Specific Claim Searches (Fact Checking)

**Run when:** User provides a quoted claim to verify or refute (1-2 searches)

```
Verify or refute the specific claim: "{exact_claim}"

web_search: "{exact_claim}"
web_search: "{exact_claim}" fact check
Optional: web_search: "{exact_claim}" debunked OR origin

Prioritize established fact-check organizations:
- Snopes (snopes.com)
- Reuters Fact Check (reuters.com/fact-check)
- AP Fact Check (apnews.com/hub/ap-fact-check)
- FactCheck.org
- PolitiFact (politifact.com)
- Full Fact (fullfact.org, UK)
- Africa Check (africacheck.org)

Also look for:
- The original source of the claim (often a misquote, oversimplification, or out-of-context excerpt of something real)
- Academic papers or primary sources that directly address the claim
- The strongest evidence FOR and AGAINST — not just the verdict

web_fetch the top 1-2 fact-check pages or primary sources for detail.

For each source, note:
- URL, outlet, date
- Source type: fact-check / academic / news / blog
- Verdict (if a fact-check): true / mostly true / mixed / mostly false / false / unproven

Return:
- The claim's verdict, weighted by source authority
- Strongest evidence each way
- The original source of the claim, if findable (or note "untraceable")
- Whether the claim is a misquote, oversimplification, or out-of-context version of a real statement
```
